"""向听数：当前手牌距离胡牌的最少摸打步数。

启发式算法：
1. 枚举每个可能的"将"（含"无将"）
2. 对剩余 tiles 做回溯分解，最大化 (完整组件数, 半组件数)
3. 距离公式：dist = 2 * (n_needed - c - d) + d + (1 if 无将 else 0)

字牌的半组件（搭子）类型：
- 对子（差 1 成坎）
- 句话两面 / 嵌张
- 特殊 2-7-10 各种二张组合
- 跨大小写对（差 1 成绞牌）
"""
from __future__ import annotations

from collections import Counter

from src.engine.components import (
    possible_components_at,
    possible_partials_at,
    subtract,
)
from src.engine.hand import Hand
from src.engine.tiles import Tile
from src.engine.win_check import is_tenpai


def shanten(hand: Hand) -> int:
    """返回向听数。0 = 听牌，1 = 一向听，..."""
    if is_tenpai(hand):
        return 0

    n_needed = 4 - len(hand.melds)
    if n_needed < 0:
        return 99

    closed = Counter(hand.closed)
    best = _shanten_with_pair_choices(closed, n_needed)
    return max(best, 1)


def _shanten_with_pair_choices(closed: Counter, n_needed: int) -> int:
    best = 99
    pair_candidates: list[Tile | None] = [
        t for t, c in closed.items() if c >= 2
    ]
    pair_candidates.append(None)

    for pair in pair_candidates:
        rem = Counter(closed)
        if pair is not None:
            rem[pair] -= 2
            if rem[pair] == 0:
                del rem[pair]
        c, d = _max_decomposition(rem, n_needed)
        if c + d > n_needed:
            d = n_needed - c
        if d < 0:
            d = 0
        no_pair_penalty = 1 if pair is None else 0
        dist = 2 * (n_needed - c - d) + d + no_pair_penalty
        if dist < best:
            best = dist
    return best


def _max_decomposition(tiles: Counter, n_needed: int) -> tuple[int, int]:
    """回溯：最大化 (完整组件, 半组件)。

    优先比较完整组件数，相同时比较半组件数。
    """
    cache: dict[tuple, tuple[int, int]] = {}
    return _backtrack(tiles, n_needed, cache)


def _backtrack(
    tiles: Counter, n_needed: int, cache: dict
) -> tuple[int, int]:
    if n_needed == 0 or not tiles:
        return (0, 0)

    key = (tuple(sorted(tiles.items())), n_needed)
    if key in cache:
        return cache[key]

    anchor = min(tiles.keys(), key=lambda t: (t.case, t.num))

    best = (0, 0)

    for comp in possible_components_at(anchor, tiles):
        new_tiles = subtract(tiles, comp)
        sub = _backtrack(new_tiles, n_needed - 1, cache)
        cand = (sub[0] + 1, sub[1])
        if cand > best:
            best = cand

    for partial in possible_partials_at(anchor, tiles):
        new_tiles = subtract(tiles, partial)
        sub = _backtrack(new_tiles, n_needed - 1, cache)
        cand = (sub[0], sub[1] + 1)
        if cand > best:
            best = cand

    new_tiles = Counter(tiles)
    new_tiles[anchor] -= 1
    if new_tiles[anchor] == 0:
        del new_tiles[anchor]
    sub = _backtrack(new_tiles, n_needed, cache)
    if sub > best:
        best = sub

    cache[key] = best
    return best
