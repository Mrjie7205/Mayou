"""胡牌判定：暗手 + 副露 + win_tile → 能否凑成 N 组件 + 1 对将。

也判定特殊胡型（小七对、双龙），天胡/地胡需要状态机配合（依赖回合/弃牌历史）。
"""
from __future__ import annotations

from collections import Counter

from src.engine.components import possible_components_at, subtract
from src.engine.hand import Hand
from src.engine.tiles import Tile


def can_win(hand: Hand, win_tile: Tile | None = None) -> bool:
    """判断胡牌（标准胡型 OR 特殊胡型）。

    - 标准胡型：暗手 + 副露 + win_tile 能拆成 4 组件 + 1 对将
    - 小七对、双龙也算胡（需在 special_hu_check 单独判，但本函数也覆盖）
    """
    if standard_can_win(hand, win_tile):
        return True
    if check_xiao_qi_dui(hand, win_tile):
        return True
    if check_shuang_long(hand, win_tile):
        return True
    return False


def standard_can_win(hand: Hand, win_tile: Tile | None = None) -> bool:
    full = Counter(hand.closed)
    if win_tile is not None:
        full[win_tile] += 1

    n_components_needed = 4 - len(hand.melds)
    if n_components_needed < 0:
        return False

    for pair_tile in list(full.keys()):
        if full[pair_tile] < 2:
            continue
        rem = Counter(full)
        rem[pair_tile] -= 2
        if rem[pair_tile] == 0:
            del rem[pair_tile]
        if _can_partition(rem, n_components_needed):
            return True
    return False


def _can_partition(tiles: Counter, n_remaining: int) -> bool:
    if n_remaining == 0:
        return sum(tiles.values()) == 0
    if not tiles:
        return False
    anchor = min(tiles.keys(), key=lambda t: (t.case, t.num))
    for component in possible_components_at(anchor, tiles):
        new_tiles = subtract(tiles, component)
        if _can_partition(new_tiles, n_remaining - 1):
            return True
    return False


def check_xiao_qi_dui(hand: Hand, win_tile: Tile | None = None) -> bool:
    """小七对：发完牌后手上有 7 对牌（无副露）。"""
    if hand.melds:
        return False
    full = Counter(hand.closed)
    if win_tile is not None:
        full[win_tile] += 1
    if sum(full.values()) != 14:
        return False
    return all(c == 2 for c in full.values()) and len(full) == 7


def check_shuang_long(hand: Hand, win_tile: Tile | None = None) -> bool:
    """双龙：手中 2 个一提（2 个 4 张相同）。

    起手就有 2 个 4 张相同的，无副露。
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
