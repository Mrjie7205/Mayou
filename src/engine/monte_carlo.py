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
            # 强制规则：摸到自对子（→ 偎）或自坎（→ 提）的牌不能立刻打，
            # 必须保留为对子/坎结构。Gemini 评审 2026-05：避免 MC 跑出违反字牌
            # 强制动作的非法局面。这里用最简化版——把这种刚摸成对/坎的牌从弃牌
            # 候选里排除，不真的转 melds（性能优先）。
            forbidden_discard = (
                drawn if sim_hand.closed.get(drawn, 0) >= 2 else None
            )
            keys = [k for k in sim_hand.closed.keys() if k != forbidden_discard]
            if not keys:
                keys = list(sim_hand.closed.keys())
            discard = rng.choice(keys)
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
