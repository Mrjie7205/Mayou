"""胡牌判定：字牌"5 门子 + 15 张 + k=m 约束"模型。

字牌胡型公式（见 docs/07 §4）：
    胡型 = 5 个门子，每个门子是 对(2) / 坎(3) / 提(4) / 句话(3) / 绞牌(3)
    总张数恒等于 15（小七对例外为 14）
    设 k=对数, m=提数, j=3张组件数，则：
        k + m + j = 5
        2k + 4m + 3j = 15
    解出 m = k，即 **对的数量必须等于提的数量**。

合法 (k, m, j) 组合只有三种：
    (0, 0, 5)：5 个 3 张组件（无对无提）
    (1, 1, 3)：1 对 + 1 提 + 3 个 3 张组件
    (2, 2, 1)：2 对 + 2 提 + 1 个 3 张组件

特殊胡型：天/地/五福归 5 门子结构（仅触发条件特殊），
小七对/双龙不属 5 门子，单独判定。
"""
from __future__ import annotations

from collections import Counter

from src.engine.components import (
    can_take_pair_at,
    can_take_ti_at,
    possible_3_components_at,
    subtract,
)
from src.engine.hand import Hand
from src.engine.tiles import Tile


def can_win(hand: Hand, win_tile: Tile | None = None) -> bool:
    if standard_can_win(hand, win_tile):
        return True
    if check_xiao_qi_dui(hand, win_tile):
        return True
    if check_shuang_long(hand, win_tile):
        return True
    return False


def standard_can_win(hand: Hand, win_tile: Tile | None = None) -> bool:
    """5 门子 + 15 张 + k=m 约束。"""
    full = Counter(hand.closed)
    if win_tile is not None:
        full[win_tile] += 1

    meld_count = len(hand.melds)
    meld_tile_count = sum(m.size for m in hand.melds)

    n_menzi_needed = 5 - meld_count
    target_tiles = 15 - meld_tile_count

    if n_menzi_needed < 0:
        return False
    if sum(full.values()) != target_tiles:
        return False

    # 副露已含的提数（提=4张组件）
    meld_ti = sum(1 for m in hand.melds if m.type in ("ti", "an_ti"))

    # 全局 k=m 约束：暗手对数 k_an = 暗手提数 m_an + meld_ti
    # 枚举 k_an ∈ [0, 2]
    for k_an in range(3):
        m_an = k_an - meld_ti
        if m_an < 0:
            continue
        j_an = n_menzi_needed - k_an - m_an
        if j_an < 0:
            continue
        # 张数验证：2*k + 4*m + 3*j == target_tiles
        if 2 * k_an + 4 * m_an + 3 * j_an != target_tiles:
            continue
        if _partition_into(full, k_an, m_an, j_an):
            return True
    return False


def _partition_into(
    tiles: Counter,
    n_pair: int,
    n_ti: int,
    n_three: int,
) -> bool:
    """按 (对, 提, 3张组件) 三元组拆 tiles。

    通过显式三元组分类避免"自由选择对子"导致违反 k=m 全局约束。
    """
    if n_pair == 0 and n_ti == 0 and n_three == 0:
        return sum(tiles.values()) == 0
    if not tiles:
        return False

    anchor = min(tiles.keys(), key=lambda t: (t.case, t.num))

    if n_pair > 0 and can_take_pair_at(anchor, tiles):
        new_tiles = subtract(tiles, (anchor, anchor))
        if _partition_into(new_tiles, n_pair - 1, n_ti, n_three):
            return True

    if n_ti > 0 and can_take_ti_at(anchor, tiles):
        new_tiles = subtract(tiles, (anchor,) * 4)
        if _partition_into(new_tiles, n_pair, n_ti - 1, n_three):
            return True

    if n_three > 0:
        for comp in possible_3_components_at(anchor, tiles):
            new_tiles = subtract(tiles, comp)
            if _partition_into(new_tiles, n_pair, n_ti, n_three - 1):
                return True

    return False


def check_xiao_qi_dui(hand: Hand, win_tile: Tile | None = None) -> bool:
    """小七对：起手 14 张恰好 7 对（无副露）。唯一 14 张胡型。"""
    if hand.melds:
        return False
    full = Counter(hand.closed)
    if win_tile is not None:
        full[win_tile] += 1
    if sum(full.values()) != 14:
        return False
    return all(c == 2 for c in full.values()) and len(full) == 7


def check_shuang_long(hand: Hand, win_tile: Tile | None = None) -> bool:
    """双龙：起手有 2 个一提（2×4=8 张同字号组），无副露。

    起手即胡，剩余 6-7 张不要求成型（字牌特殊起手胡）。
    """
    if hand.melds:
        return False
    full = Counter(hand.closed)
    if win_tile is not None:
        full[win_tile] += 1
    fours = sum(1 for c in full.values() if c == 4)
    return fours >= 2


def waiting_tiles(hand: Hand) -> list[Tile]:
    """听张：能让你胡的所有牌。"""
    from src.engine.tiles import ALL_KINDS
    return [k for k in ALL_KINDS if can_win(hand, k)]


def is_tenpai(hand: Hand) -> bool:
    return bool(waiting_tiles(hand))
