"""蒙特卡洛进攻评分。

对每张可打牌：
1. 假装打出去（暗手减一张）
2. 模拟若干次"摸打"序列，看自己胡的概率和期望积分
3. 对手用最简单启发式（随机弃 / 不胡 / 不影响牌山）

Sprint 6 阶段先做最小可行版本，Sprint 8 调参。
"""
from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass

from src.engine.hand import Hand
from src.engine.score import (
    SOURCE_SELF_DRAW,
    WinScore,
    estimate_win_kind,
)
from src.engine.shanten import shanten
from src.engine.tiles import ALL_KINDS, DECK_COUNT_PER_KIND, Tile
from src.engine.win_check import can_win, waiting_tiles


DEFAULT_SIMULATIONS = 300  # MVP；Sprint 8 调到 1000+
DEFAULT_LOOKAHEAD = 12     # Gemini 评审：8 步太浅，调到 12 让模拟更接近终局


@dataclass
class AttackScore:
    tile: Tile
    win_prob: float
    expected_score: float
    shanten_after: int

    @property
    def composite(self) -> float:
        # 简单加权：胡概率占主，期望积分归一化加补
        return self.win_prob * 0.7 + min(self.expected_score / 30.0, 1.0) * 0.3


def remaining_tile_pool(
    hand: Hand,
    visible_tiles: Counter,
) -> Counter:
    """剩余可摸牌池 = 全副 - 自己暗手 - 全场可见。

    visible_tiles 应是「全场可见」(4 家弃牌 + 4 家副露，含自己副露)。
    自己暗手单独计入，避免重复减。
    """
    pool = Counter({k: DECK_COUNT_PER_KIND for k in ALL_KINDS})
    for t, c in hand.closed.items():
        pool[t] -= c
    for t, c in visible_tiles.items():
        pool[t] -= c
    for t in list(pool.keys()):
        if pool[t] <= 0:
            del pool[t]
    return pool


def _draw_random(pool: Counter, rng: random.Random) -> Tile | None:
    if not pool:
        return None
    tiles = list(pool.elements())
    return rng.choice(tiles)


def _fast_eval_discard(
    hand_closed: Counter,
    rng: random.Random,
    *,
    forbidden: Tile | None = None,
) -> Tile | None:
    """启发式选要打的牌（Wave 1.3，见 ADR-003）。

    替代之前的 random_choice，让 MC 模拟更接近真实玩家决策。
    策略（按优先级）：
    1. 排除 forbidden（刚摸到的对/坎张，强制偎/提）
    2. 优先打孤张（count==1 且无相邻搭子）
    3. 次优先：边缘字号（num=1 或 10）的散张
    4. 红色字号尽量留（除非真孤立）
    5. top-2 候选间用 rng 选择，保持模拟多样性

    复杂度 O(n_kinds)，单次调用 < 0.1ms。
    """
    candidates = [t for t in hand_closed if t != forbidden]
    if not candidates:
        candidates = list(hand_closed.keys())
    if not candidates:
        return None

    def has_neighbor(t: Tile) -> bool:
        for delta in (-1, 1):
            n = t.num + delta
            if 1 <= n <= 10:
                if hand_closed.get(Tile(t.case, n), 0) > 0:
                    return True
        # 特殊连张 2-7-10
        if t.num in (2, 7, 10):
            partners = {2, 7, 10} - {t.num}
            for n in partners:
                if hand_closed.get(Tile(t.case, n), 0) > 0:
                    return True
        # 同 num 异 case (绞牌搭子)
        other_case = "U" if t.case == "L" else "L"
        if t.num not in (2, 7, 10):
            if hand_closed.get(Tile(other_case, t.num), 0) > 0:
                return True
        return False

    def discard_priority(t: Tile) -> float:
        count = hand_closed[t]
        score = 0.0
        if count == 1:
            score += 2.0          # 孤张优先
        if count >= 2:
            score -= 3.0          # 有对/坎不能轻易拆
        if not has_neighbor(t) and count == 1:
            score += 2.0          # 真孤立
        if t.num in (1, 10):
            score += 0.3          # 边缘略优
        if t.is_red:
            score -= 0.8          # 红牌珍贵
        return score

    ranked = sorted(candidates, key=discard_priority, reverse=True)
    top_k = ranked[: min(2, len(ranked))]
    return rng.choice(top_k)


def evaluate_attack(
    hand: Hand,
    discard_tile: Tile,
    visible_tiles: Counter,
    *,
    simulations: int = DEFAULT_SIMULATIONS,
    lookahead: int = DEFAULT_LOOKAHEAD,
    rng: random.Random | None = None,
) -> AttackScore:
    """打掉 discard_tile 后的进攻评估。"""
    rng = rng or random.Random()

    after_hand = hand.copy()
    after_hand.remove(discard_tile)
    sh = shanten(after_hand)

    # 听牌时直接算等待张概率，不需要模拟
    if sh == 0:
        waits = waiting_tiles(after_hand)
        pool = remaining_tile_pool(after_hand, visible_tiles)
        n_wait = sum(pool[w] for w in waits)
        n_total = sum(pool.values())
        win_prob = n_wait / n_total if n_total else 0.0
        kind = estimate_win_kind(after_hand)
        expected = WinScore.for_normal_win(kind, SOURCE_SELF_DRAW).total_received
        return AttackScore(discard_tile, win_prob, expected * win_prob, sh)

    # 多向听做轻量蒙特卡洛
    pool = remaining_tile_pool(after_hand, visible_tiles)
    wins = 0
    total_score = 0.0
    for _ in range(simulations):
        sim_hand = after_hand.copy()
        sim_pool = Counter(pool)
        won = False
        for _step in range(lookahead):
            drawn = _draw_random(sim_pool, rng)
            if drawn is None:
                break
            sim_pool[drawn] -= 1
            if sim_pool[drawn] == 0:
                del sim_pool[drawn]
            if can_win(sim_hand, drawn):
                wins += 1
                kind = estimate_win_kind(sim_hand)
                total_score += WinScore.for_normal_win(
                    kind, SOURCE_SELF_DRAW
                ).total_received
                won = True
                break
            sim_hand.add(drawn)
            # 强制规则：摸到自对子（→ 偎）或自坎（→ 提）的牌不能立刻打
            forbidden_discard = (
                drawn if sim_hand.closed.get(drawn, 0) >= 2 else None
            )
            # Wave 1.3：用启发式替代纯随机，避免自杀式弃高危红牌
            discard = _fast_eval_discard(
                sim_hand.closed, rng, forbidden=forbidden_discard,
            )
            if discard is None:
                break
            sim_hand.remove(discard)
        if not won:
            pass
    win_prob = wins / simulations
    expected = (total_score / wins) if wins else 0.0
    return AttackScore(discard_tile, win_prob, expected * win_prob, sh)


def evaluate_all_discards(
    hand: Hand,
    visible_tiles: Counter,
    *,
    simulations: int = DEFAULT_SIMULATIONS,
    rng: random.Random | None = None,
) -> list[AttackScore]:
    """对手中每种可打牌跑一遍蒙特卡洛，返回排序后的列表。"""
    rng = rng or random.Random()
    scores: list[AttackScore] = []
    for tile in list(hand.closed.keys()):
        scores.append(
            evaluate_attack(
                hand, tile, visible_tiles,
                simulations=simulations, rng=rng,
            )
        )
    scores.sort(key=lambda s: s.composite, reverse=True)
    return scores
