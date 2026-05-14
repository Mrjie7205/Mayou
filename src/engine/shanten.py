"""向听数：当前手牌距离胡牌的最少摸打步数。

字牌胡型 = 5 门子 + k=m + 15 张（见 win_check.py）。
shanten 是启发式估算，不严格受 k=m 约束（用于推断"距离听牌多远"），
最终精确判断仍由 win_check.can_win 完成。

距离公式：
    distance = max(2 * (n_menzi - c - d) + d, 0)
其中：
    n_menzi  = 5 - len(melds)：还要凑的门子数
    c        = 暗手能拆出的完整门子数（对 / 坎 / 提 / 句话 / 绞牌）
    d        = 半门子数（差 1 张能升完整门子）
若 shanten == 0 → 听牌或已胡。
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
from src.engine.win_check import can_win, is_tenpai


def shanten(hand: Hand) -> int:
    if can_win(hand):
        return 0
    if is_tenpai(hand):
        return 0

    n_menzi_needed = 5 - len(hand.melds)
    if n_menzi_needed < 0:
        return 99

    closed = Counter(hand.closed)
    cache: dict[tuple, tuple[int, int]] = {}
    c, d = _max_decomposition(closed, n_menzi_needed, cache)

    if c + d > n_menzi_needed:
        d = n_menzi_needed - c
    if d < 0:
        d = 0
    dist = 2 * (n_menzi_needed - c - d) + d
    return max(dist, 1)


def _max_decomposition(
    tiles: Counter,
    n_needed: int,
    cache: dict,
) -> tuple[int, int]:
    """回溯找最大化 (完整门子数, 半门子数)。

    字牌特有：对子既可以是完整门子（在 k=m 约束允许时），
    也可以是半门子（差 1 张升坎/绞牌）。
    本函数不严格执行 k=m，是启发式估算，用于 shanten。
    """
    if n_needed == 0 or not tiles:
        return (0, 0)

    key = (tuple(sorted(tiles.items())), n_needed)
    if key in cache:
        return cache[key]

    anchor = min(tiles.keys(), key=lambda t: (t.case, t.num))
    best = (0, 0)

    # 对作为完整门子
    if tiles[anchor] >= 2:
        new_tiles = subtract(tiles, (anchor, anchor))
        sub = _max_decomposition(new_tiles, n_needed - 1, cache)
        cand = (sub[0] + 1, sub[1])
        if cand > best:
            best = cand

    # 坎/提/句话/绞牌作为完整门子
    for comp in possible_components_at(anchor, tiles):
        new_tiles = subtract(tiles, comp)
        sub = _max_decomposition(new_tiles, n_needed - 1, cache)
        cand = (sub[0] + 1, sub[1])
        if cand > best:
            best = cand

    # 半门子（差 1 张能成完整门子）
    for partial in possible_partials_at(anchor, tiles):
        new_tiles = subtract(tiles, partial)
        sub = _max_decomposition(new_tiles, n_needed - 1, cache)
        cand = (sub[0], sub[1] + 1)
        if cand > best:
            best = cand

    # anchor 作散张
    new_tiles = Counter(tiles)
    new_tiles[anchor] -= 1
    if new_tiles[anchor] == 0:
        del new_tiles[anchor]
    sub = _max_decomposition(new_tiles, n_needed, cache)
    if sub > best:
        best = sub

    cache[key] = best
    return best
