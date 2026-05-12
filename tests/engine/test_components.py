from collections import Counter

from src.engine.components import (
    is_jiao,
    is_jvhua,
    possible_components_at,
    possible_partials_at,
)
from src.engine.tiles import Tile


def test_jvhua_consecutive_lower():
    assert is_jvhua((Tile("L", 1), Tile("L", 2), Tile("L", 3)))
    assert is_jvhua((Tile("L", 8), Tile("L", 9), Tile("L", 10)))


def test_jvhua_consecutive_upper():
    assert is_jvhua((Tile("U", 5), Tile("U", 6), Tile("U", 7)))


def test_jvhua_special_2_7_10():
    assert is_jvhua((Tile("L", 2), Tile("L", 7), Tile("L", 10)))
    assert is_jvhua((Tile("U", 2), Tile("U", 7), Tile("U", 10)))


def test_jvhua_no_cross_case():
    assert not is_jvhua((Tile("L", 1), Tile("L", 2), Tile("U", 3)))


def test_jvhua_not_consecutive():
    assert not is_jvhua((Tile("L", 1), Tile("L", 3), Tile("L", 5)))


def test_jiao_basic():
    # 一对小九 + 一张大玖
    assert is_jiao((Tile("L", 9), Tile("L", 9), Tile("U", 9)))
    # 一对大伍 + 一张小五
    assert is_jiao((Tile("L", 5), Tile("U", 5), Tile("U", 5)))


def test_jiao_red_forbidden():
    # 红色字号 2/7/10 不能跨大小写绞
    assert not is_jiao((Tile("L", 2), Tile("L", 2), Tile("U", 2)))
    assert not is_jiao((Tile("L", 7), Tile("L", 7), Tile("U", 7)))
    assert not is_jiao((Tile("L", 10), Tile("L", 10), Tile("U", 10)))


def test_jiao_same_case_not_jiao():
    # 三张相同小九：是坎不是绞
    assert not is_jiao((Tile("L", 9), Tile("L", 9), Tile("L", 9)))


def test_components_at_anchor_triplet():
    tiles = Counter([Tile("L", 5)] * 3)
    comps = list(possible_components_at(Tile("L", 5), tiles))
    assert (Tile("L", 5), Tile("L", 5), Tile("L", 5)) in comps


def test_components_at_anchor_jvhua():
    tiles = Counter([Tile("L", 1), Tile("L", 2), Tile("L", 3)])
    comps = list(possible_components_at(Tile("L", 1), tiles))
    assert (Tile("L", 1), Tile("L", 2), Tile("L", 3)) in comps


def test_components_at_anchor_special_jvhua():
    tiles = Counter([Tile("U", 2), Tile("U", 7), Tile("U", 10)])
    comps = list(possible_components_at(Tile("U", 2), tiles))
    assert (Tile("U", 2), Tile("U", 7), Tile("U", 10)) in comps


def test_components_at_anchor_jiao():
    # L5 L5 U5 → 绞牌
    tiles = Counter([Tile("L", 5), Tile("L", 5), Tile("U", 5)])
    comps = list(possible_components_at(Tile("L", 5), tiles))
    assert (Tile("L", 5), Tile("L", 5), Tile("U", 5)) in comps


def test_partials_pair():
    tiles = Counter([Tile("L", 5), Tile("L", 5)])
    parts = list(possible_partials_at(Tile("L", 5), tiles))
    assert (Tile("L", 5), Tile("L", 5)) in parts


def test_partials_two_consecutive():
    tiles = Counter([Tile("L", 5), Tile("L", 6)])
    parts = list(possible_partials_at(Tile("L", 5), tiles))
    assert (Tile("L", 5), Tile("L", 6)) in parts
