"""综合推荐：进攻分 + 防守分 → 综合分排序。

α、β 权重根据局势动态调整：
- 自己已听 → α 大幅升高
- 对手疑似听 / 五福报警 → β 升高
- 否则均衡
"""
from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass
from typing import Optional

from src.engine.defense import DefenseScore, OpponentInfo, evaluate_all as eval_defense
from src.engine.hand import Hand
from src.engine.monte_carlo import (
    AttackScore,
    DEFAULT_SIMULATIONS,
    evaluate_all_discards,
)
from src.engine.shanten import shanten
from src.engine.tiles import Tile


@dataclass
class Recommendation:
    tile: Tile
    attack: AttackScore
    defense: DefenseScore
    combined: float
    rank: int = 0


def determine_weights(
    hand: Hand,
    opponents: dict[str, OpponentInfo],
) -> tuple[float, float]:
    """根据局势返回 (α, β)，满足 α + β = 1。"""
    own_shanten = shanten(hand)
    any_baojing = any(opp.is_baojing for opp in opponents.values())

    if own_shanten == 0:
        # 自己已听：拼进攻
        return (0.85, 0.15)
    if any_baojing:
        # 对手五福报警：拼防守
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

    recs: list[Recommendation] = []
    for tile in candidates:
        a = attack_by_tile[tile]
        d = defense_by_tile[tile]
        combined = a.composite * alpha + d.safety * beta
        recs.append(Recommendation(tile, a, d, combined))

    recs.sort(key=lambda r: r.combined, reverse=True)
    for i, r in enumerate(recs):
        r.rank = i + 1
    return recs
