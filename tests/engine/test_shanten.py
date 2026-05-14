"""shanten 测试（基于 5 门子模型）。"""
from src.engine.hand import Hand
from src.engine.shanten import shanten
from src.engine.tiles import Tile, parse_many


def hand_from(codes):
    return Hand.from_tiles(parse_many(codes))


def test_already_won_shanten_zero():
    """15 张已成 5 门子胡型 → shanten=0。"""
    codes = [
        "L1", "L2", "L3",
        "L4", "L5", "L6",
        "L7", "L8", "L9",
        "U1", "U2", "U3",
        "U5", "U6", "U7",
    ]
    assert shanten(hand_from(codes)) == 0


def test_14_tile_tenpai_one_away():
    """14 张离 5 门子差 1 张 → shanten=0（听牌）。"""
    codes = [
        "L1", "L2", "L3",
        "L4", "L5", "L6",
        "L7", "L8", "L9",
        "U1", "U2", "U3",
        "U5", "U6",
    ]
    assert shanten(hand_from(codes)) == 0


def test_one_shanten_small():
    """13 张离听 1 步：摸 1 张能听。"""
    codes = [
        "L1", "L2", "L3",
        "L4", "L5", "L6",
        "L7", "L8", "L9",
        "U1", "U2", "U3",
        "U5",
    ]
    s = shanten(hand_from(codes))
    assert 0 <= s <= 2


def test_garbage_hand_high_shanten():
    codes = [
        "L1", "L3", "L5", "L7", "L9",
        "U2", "U4", "U6", "U8", "U10",
        "L4", "L6", "L8",
    ]
    s = shanten(hand_from(codes))
    assert s >= 1


def test_pair_without_ti_demoted_to_partial():
    """Gemini 评审补丁：副露 4 组无提 + 暗手对+1散 → 违反 k=m，shanten 应 ≥ 1。

    副露占 4 门子（无提），暗手需要 1 个 3 张组件凑第 5 门子。
    但暗手是 1 对 + 1 散 → 对子无对应提，不能算完整门子。
    旧 shanten 会把对子当完整门子算 shanten=0（偏乐观），新版应正确判 ≥ 1。
    """
    from src.engine.hand import Meld
    melds = [
        Meld("an_ke", (Tile("L", 6),) * 3),
        Meld("chi_jvhua", (Tile("U", 1), Tile("U", 2), Tile("U", 3))),
        Meld("chi_jvhua", (Tile("U", 4), Tile("U", 5), Tile("U", 6))),
        Meld("chi_jvhua", (Tile("U", 7), Tile("U", 8), Tile("U", 9))),
    ]
    codes = ["L10", "L10", "L5"]  # 大拾对 + 小伍单
    hand = Hand.from_tiles(parse_many(codes), melds)
    s = shanten(hand)
    assert s >= 1, f"对子无提应被降级为半门子，但 shanten={s}（偏乐观）"


def test_2_pair_without_2_ti_demoted():
    """更极端：副露 3 组无提 + 暗手 3 对 → 违反 k=m，shanten ≥ 1。"""
    from src.engine.hand import Meld
    melds = [
        Meld("an_ke", (Tile("L", 6),) * 3),
        Meld("chi_jvhua", (Tile("U", 1), Tile("U", 2), Tile("U", 3))),
        Meld("chi_jvhua", (Tile("U", 4), Tile("U", 5), Tile("U", 6))),
    ]
    codes = ["L10", "L10", "L5", "L5", "U10", "U10"]  # 3 对（无提配对）
    hand = Hand.from_tiles(parse_many(codes), melds)
    s = shanten(hand)
    assert s >= 1


def test_pair_with_ti_can_be_full_menzi():
    """有提时对子可作完整门子（k=m=1 合法）。

    副露含 1 提 + 暗手对 + 3 个 3 张 = 5 门子 (k=1, m=1, j=3) → 胡（shanten=0）。
    """
    from src.engine.hand import Meld
    melds = [Meld("ti", (Tile("L", 6),) * 4)]
    codes = [
        "L1", "L2", "L3",
        "U1", "U2", "U3",
        "U5", "U6", "U7",
        "U10", "U10",
    ]
    hand = Hand.from_tiles(parse_many(codes), melds)
    s = shanten(hand)
    assert s == 0
