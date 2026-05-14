"""向听数：当前手牌距离胡牌的最少摸打步数。

字牌胡型 = 5 门子 + k=m + 15 张（见 win_check.py）。
shanten 是启发式估算，**通过限制"对子作完整门子"次数 ≤ 理论最大提数**
近似满足 k=m 约束（Gemini 评审 2026-05 建议）。

距离公式：
    distance = max(2 * (n_menzi - c - d) + d, 0)
其中：
    n_menzi          = 5 - len(melds)：还要凑的门子数
    c                = 暗手能拆出的完整门子数（对 / 坎 / 提 / 句话 / 绞牌）
    d                = 半门子数（差 1 张能升完整门子）
    max_pair_as_full = 暗手对子能作完整门子的上限 = 副露提数 + 暗手 4 张相同牌组数
    超过 max_pair_as_full 的对子只能走半门子（升坎 / 升绞牌）

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

    # Gemini 评审：限制对子作完整门子的次数 ≤ 理论最大提数
    # k=m 全局约束 → k ≤ M_max（M_max = 已有提 + 暗手 4 张牌组数）
    meld_ti = sum(1 for m in hand.melds if m.type in ("ti", "an_ti"))
    closed_4tile_groups = sum(1 for c in closed.values() if c >= 4)
    max_pair_as_full = meld_ti + closed_4tile_groups

    cache: dict[tuple, tuple[int, int]] = {}
    c, d = _max_decomposition(
        closed, n_menzi_needed, max_pair_as_full, 0, cache,
    )

    if c + d > n_menzi_needed:
        d = n_menzi_needed - c
    if d < 0:
        d = 0
    dist = 2 * (n_menzi_needed - c - d) + d
    return max(dist, 1)


def _max_decomposition(
    tiles: Counter,
    n_needed: int,
    max_pair_as_full: int,
    pair_used: int,
    cache: dict,
) -> tuple[int, int]:
    """回溯找最大化 (完整门子数, 半门子数)。

    `pair_used` 跟踪已用作完整门子的对子数，必须 < max_pair_as_full
    才能再把对子算作完整门子；超出时对子只能走半门子分支。
    这避免了"5 对没提"被误判为接近胡。
    """
    if n_needed == 0 or not tiles:
        return (0, 0)

    key = (tuple(sorted(tiles.items())), n_needed, pair_used)
    if key in cache:
        return cache[key]

    anchor = min(tiles.keys(), key=lambda t: (t.case, t.num))
    best = (0, 0)

    # 对作为完整门子（受 max_pair_as_full 限制）
    if tiles[anchor] >= 2 and pair_used < max_pair_as_full:
        new_tiles = subtract(tiles, (anchor, anchor))
        sub = _max_decomposition(
            new_tiles, n_needed - 1, max_pair_as_full, pair_used + 1, cache,
        )
        cand = (sub[0] + 1, sub[1])
        if cand > best:
            best = cand

    # 坎/提/句话/绞牌作为完整门子
    for comp in possible_components_at(anchor, tiles):
        new_tiles = subtract(tiles, comp)
        sub = _max_decomposition(
            new_tiles, n_needed - 1, max_pair_as_full, pair_used, cache,
        )
        cand = (sub[0] + 1, sub[1])
        if cand > best:
            best = cand

    # 半门子（差 1 张能成完整门子）—— 含对子作半门子的分支
    for partial in possible_partials_at(anchor, tiles):
        new_tiles = subtract(tiles, partial)
        sub = _max_decomposition(
            new_tiles, n_needed - 1, max_pair_as_full, pair_used, cache,
        )
        cand = (sub[0], sub[1] + 1)
        if cand > best:
            best = cand

    # anchor 作散张
    new_tiles = Counter(tiles)
    new_tiles[anchor] -= 1
    if new_tiles[anchor] == 0:
        del new_tiles[anchor]
    sub = _max_decomposition(
        new_tiles, n_needed, max_pair_as_full, pair_used, cache,
    )
    if sub > best:
        best = sub

    cache[key] = best
    return best
