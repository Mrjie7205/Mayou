"""综合推荐：Net EV (Expected Value) 驱动。

Wave 1.1（ADR-003）：废弃静态加权 `α × attack + β × defense`，
改用绝对期望收益：

    EV(T) = (我胡概率 × 我胡的预期得分) - max(对手 i 胡概率 × 放炮失分_i)

字牌得分指数爆炸（普通胡 12 分 vs 五福 120 分），线性加权无法
正确权衡"高安全度但巨额失分"和"低安全度但小额失分"。

对手「胡概率」用 estimate_opponent_shanten 粗估（向听越低概率越高）。
放炮失分按对手类型分档（普通/三大/五福报警）。
"""
from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass
from typing import Optional

from src.engine.defense import (
    DefenseScore,
    OpponentInfo,
    estimate_opponent_shanten,
    evaluate_all as eval_defense,
)
from src.engine.hand import Hand
from src.engine.monte_carlo import (
    AttackScore,
    DEFAULT_SIMULATIONS,
    evaluate_all_discards,
)
from src.engine.shanten import shanten
from src.engine.tiles import Tile


# 放炮失分档位（按对手当前状态预估）
LOSS_PUTONG_HU = 12       # 普通胡放炮基础
LOSS_PENG_HU = 15         # 碰牌胡放炮
LOSS_PAO_HU = 24          # 跑牌胡放炮
LOSS_WU_FU = 120          # 五福放炮（极端）
LOSS_BAOJING_DEFAULT = 60 # 报警家放炮的混合预期（五福或跑胡）


@dataclass
class Recommendation:
    tile: Tile
    attack: AttackScore
    defense: DefenseScore
    ev_my: float           # 我胡的期望得分（win_prob × per_win_score）
    ev_loss: float         # 放炮预期失分
    ev: float              # 净期望 = ev_my - ev_loss
    combined: float        # 兼容字段：归一化后的 0-1 分（供旧 UI 用）
    rank: int = 0


def estimate_loss_per_seat(opp: OpponentInfo) -> float:
    """估算给该家放炮时的预期失分。"""
    if opp.is_baojing:
        return LOSS_BAOJING_DEFAULT
    if opp.peng_count >= 3:
        # 三大状态，他可能凑五福，但失分上限有限
        return LOSS_PAO_HU * 1.5  # 36
    if opp.peng_count >= 1:
        return LOSS_PENG_HU
    return LOSS_PUTONG_HU


def estimate_opp_win_prob_factor(opp: OpponentInfo) -> float:
    """对手当前胡牌"威胁系数" ∈ [0..1]。

    用 estimate_opponent_shanten 反推：向听越低系数越高。
    实际 P(对手胡 这张) = 系数 × (1 - safety)，由 EV 公式分别使用。
    """
    sh = estimate_opponent_shanten(opp)
    if sh <= 1:
        return 1.0   # 接近听，威胁满
    if sh == 2:
        return 0.7
    if sh == 3:
        return 0.4
    if sh == 4:
        return 0.2
    return 0.1


def determine_weights(
    hand: Hand,
    opponents: dict[str, OpponentInfo],
) -> tuple[float, float]:
    """旧的 (α, β) 配置 — 仅给 combined 兼容字段用，新代码用 EV。"""
    own_shanten = shanten(hand)
    any_baojing = any(opp.is_baojing for opp in opponents.values())
    if own_shanten == 0:
        return (0.85, 0.15)
    if any_baojing:
        return (0.3, 0.7)
    if own_shanten == 1:
        return (0.65, 0.35)
    return (0.55, 0.45)


def recommend(
    hand: Hand,
    opponents: dict[str, OpponentInfo],
    all_visible: Counter,
    *,
    simulations: int = DEFAULT_SIMULATIONS,
    rng: Optional[random.Random] = None,
) -> list[Recommendation]:
    rng = rng or random.Random()
    candidates = list(hand.closed.keys())

    attack_scores = evaluate_all_discards(
        hand, all_visible, simulations=simulations, rng=rng
    )
    attack_by_tile = {a.tile: a for a in attack_scores}

    defense_scores = eval_defense(candidates, opponents, all_visible)
    defense_by_tile = {d.tile: d for d in defense_scores}

    alpha, beta = determine_weights(hand, opponents)

    # 预算每家的放炮失分档
    loss_by_seat = {
        seat: estimate_loss_per_seat(opp) * estimate_opp_win_prob_factor(opp)
        for seat, opp in opponents.items()
    }

    recs: list[Recommendation] = []
    for tile in candidates:
        a = attack_by_tile[tile]
        d = defense_by_tile[tile]

        # 我胡的期望（attack.expected_score 已经是 per_win × win_prob）
        ev_my = a.expected_score

        # 放炮预期失分：对每家算 (1 - per_seat_safety) × per_seat_loss，取最大
        ev_loss = 0.0
        for seat, opp_loss in loss_by_seat.items():
            seat_safety = d.per_seat.get(seat, 1.0)
            seat_threat = (1.0 - seat_safety) * opp_loss
            if seat_threat > ev_loss:
                ev_loss = seat_threat

        ev = ev_my - ev_loss

        # 兼容字段：旧线性加权（UI 仍能读到，但不参与排序）
        combined = a.composite * alpha + d.safety * beta

        recs.append(Recommendation(
            tile=tile, attack=a, defense=d,
            ev_my=ev_my, ev_loss=ev_loss, ev=ev,
            combined=combined,
        ))

    # 按 EV 降序
    recs.sort(key=lambda r: r.ev, reverse=True)
    for i, r in enumerate(recs):
        r.rank = i + 1
    return recs
