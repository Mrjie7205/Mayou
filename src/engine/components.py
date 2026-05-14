"""字牌组件枚举：句话 / 绞牌 / 坎 / 提，以及拆分时的"半组件"（搭子）。

**约定**：组件枚举时 `anchor` 始终是组件的最小元素（按 (case, num) 字典序）。
这是回溯拆分的不变式——每次都从剩余 tiles 的最小元素开始挑下一组件。
"""
from __future__ import annotations

from collections import Counter
from typing import Iterator

from src.engine.tiles import Tile


RED_NUMS = frozenset({2, 7, 10})


def is_jvhua(triple: tuple[Tile, Tile, Tile]) -> bool:
    """三张牌（任意顺序）是否构成一句话。"""
    sorted_t = sorted(triple, key=lambda t: (t.case, t.num))
    if sorted_t[0].case != sorted_t[1].case or sorted_t[1].case != sorted_t[2].case:
        return False
    nums = tuple(t.num for t in sorted_t)
    if nums == (nums[0], nums[0] + 1, nums[0] + 2):
        return True
    if nums == (2, 7, 10):
        return True
    return False


def is_jiao(triple: tuple[Tile, Tile, Tile]) -> bool:
    """三张牌是否构成绞牌（1 对 + 1 张同 num 异 case）。"""
    sorted_t = sorted(triple, key=lambda t: (t.case, t.num))
    nums = {t.num for t in sorted_t}
    if len(nums) != 1:
        return False
    n = sorted_t[0].num
    if n in RED_NUMS:
        return False
    cases = [t.case for t in sorted_t]
    # 一个 case 出现 2 次，另一个出现 1 次
    case_count = Counter(cases)
    return sorted(case_count.values()) == [1, 2]


def possible_components_at(anchor: Tile, tiles: Counter) -> Iterator[tuple[Tile, ...]]:
    """枚举所有以 anchor 为最小元素、可从 tiles 中取出的完整组件。

    yields 每个组件按 (case, num) 排序的 tuple。

    含坎(3) / 提(4) / 句话(3) / 绞牌(3) 全部。用于不区分门子类型的场景。
    """
    case, num = anchor.case, anchor.num

    # 坎（3 张相同）
    if tiles[anchor] >= 3:
        yield (anchor, anchor, anchor)

    # 提（4 张相同）
    if tiles[anchor] >= 4:
        yield (anchor, anchor, anchor, anchor)

    # 句话：普通连续 anchor, anchor+1, anchor+2
    if num <= 8:
        b, c = Tile(case, num + 1), Tile(case, num + 2)
        if tiles[b] >= 1 and tiles[c] >= 1:
            yield (anchor, b, c)

    # 句话：特殊 2-7-10（anchor 必为 num=2 才以 anchor 起头）
    if num == 2:
        b, c = Tile(case, 7), Tile(case, 10)
        if tiles[b] >= 1 and tiles[c] >= 1:
            yield (anchor, b, c)

    # 绞牌：anchor.case == "L"（U 不可能是 min 同时绞牌还需要异色更小）
    other = "U" if case == "L" else "L"
    if num not in RED_NUMS:
        partner = Tile(other, num)
        # 形态 (anchor, anchor, partner)：anchor 在对子里
        if tiles[anchor] >= 2 and tiles[partner] >= 1 and case == "L":
            yield (anchor, anchor, partner)
        # 形态 (anchor, partner, partner)：anchor 是单张，partner 在对子
        if tiles[anchor] >= 1 and tiles[partner] >= 2 and case == "L":
            yield (anchor, partner, partner)


def possible_3_components_at(anchor: Tile, tiles: Counter) -> Iterator[tuple[Tile, ...]]:
    """仅 3 张组件（坎 / 句话 / 绞牌）。**不含提**。

    用于按 (k, m, j) 分类拆解时的 j 分支：j 代表"3 张组件门子数"。
    """
    case, num = anchor.case, anchor.num

    # 坎
    if tiles[anchor] >= 3:
        yield (anchor, anchor, anchor)

    # 句话普通
    if num <= 8:
        b, c = Tile(case, num + 1), Tile(case, num + 2)
        if tiles[b] >= 1 and tiles[c] >= 1:
            yield (anchor, b, c)

    # 句话 2-7-10 特殊
    if num == 2:
        b, c = Tile(case, 7), Tile(case, 10)
        if tiles[b] >= 1 and tiles[c] >= 1:
            yield (anchor, b, c)

    # 绞牌（仅 anchor.case=="L" 起头）
    other = "U" if case == "L" else "L"
    if num not in RED_NUMS and case == "L":
        partner = Tile(other, num)
        if tiles[anchor] >= 2 and tiles[partner] >= 1:
            yield (anchor, anchor, partner)
        if tiles[anchor] >= 1 and tiles[partner] >= 2:
            yield (anchor, partner, partner)


def can_take_ti_at(anchor: Tile, tiles: Counter) -> bool:
    """anchor 能否作为提（4 张相同）的起点。"""
    return tiles[anchor] >= 4


def can_take_pair_at(anchor: Tile, tiles: Counter) -> bool:
    """anchor 能否作为对（2 张相同）的起点。"""
    return tiles[anchor] >= 2


def possible_partials_at(anchor: Tile, tiles: Counter) -> Iterator[tuple[Tile, ...]]:
    """枚举以 anchor 为最小元素的"搭子"（差 1 张能成完整组件）。

    用于 shanten 启发式估算。
    """
    case, num = anchor.case, anchor.num

    # 对子（差 1 成坎）
    if tiles[anchor] >= 2:
        yield (anchor, anchor)

    # 句话搭子：anchor + anchor+1（差 anchor+2 或 anchor-1）
    if num <= 9:
        b = Tile(case, num + 1)
        if tiles[b] >= 1:
            yield (anchor, b)

    # 句话搭子：anchor + anchor+2（差 anchor+1，"嵌张"）
    if num <= 8:
        b = Tile(case, num + 2)
        if tiles[b] >= 1:
            yield (anchor, b)

    # 特殊 2-7-10 搭子
    if num == 2:
        b7, b10 = Tile(case, 7), Tile(case, 10)
        if tiles[b7] >= 1:
            yield (anchor, b7)
        if tiles[b10] >= 1:
            yield (anchor, b10)
    if num == 7:
        b10 = Tile(case, 10)
        if tiles[b10] >= 1:
            yield (anchor, b10)

    # 绞牌搭子：跨大小写对（anchor + 异色同 num，差 1 张同 case 同 num 升对子）
    other = "U" if case == "L" else "L"
    if num not in RED_NUMS and case == "L":
        partner = Tile(other, num)
        if tiles[partner] >= 1:
            yield (anchor, partner)


def subtract(tiles: Counter, taken: tuple[Tile, ...]) -> Counter:
    new = Counter(tiles)
    for t in taken:
        new[t] -= 1
        if new[t] == 0:
            del new[t]
        elif new[t] < 0:
            raise ValueError(f"取出超过持有: {t}")
    return new
