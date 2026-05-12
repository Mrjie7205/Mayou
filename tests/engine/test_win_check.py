from src.engine.hand import Hand, Meld
from src.engine.tiles import Tile, parse_many
from src.engine.win_check import (
    can_win,
    check_shuang_long,
    check_xiao_qi_dui,
    is_tenpai,
    standard_can_win,
    waiting_tiles,
)


def hand_from(codes: list[str], melds: list[Meld] | None = None) -> Hand:
    return Hand.from_tiles(parse_many(codes), melds or [])


def test_simple_jvhua_win():
    # 4 句话 + 1 对将（全在暗手里）
    codes = [
        "L1", "L2", "L3",
        "L4", "L5", "L6",
        "L7", "L8", "L9",
        "U1", "U2", "U3",
    ]
    hand = hand_from(codes)
    # 暗手 12 张，加 win_tile（成将的第二张）共 14 张
    # 14 张组成：4 句话 + 1 对将 → 需将一对
    # 修：12 张里没有对，加一张同时成将组件不可能
    # 所以这测试改为 13 张暗手 + win_tile 成将
    codes13 = codes + ["U4"]
    hand = hand_from(codes13)
    assert can_win(hand, Tile("U", 4))  # win_tile=U4 凑成 U4-U4 将


def test_kan_win():
    # 4 个坎 + 1 对将
    codes = [
        "L1", "L1", "L1",
        "L5", "L5", "L5",
        "U3", "U3", "U3",
        "U8", "U8", "U8",
        "L7",
    ]
    hand = hand_from(codes)
    assert can_win(hand, Tile("L", 7))  # win_tile 成将


def test_with_peng_meld():
    # 副露：碰 L5×3。暗手：3 句话 + 1 对将
    melds = [Meld("peng", (Tile("L", 5), Tile("L", 5), Tile("L", 5)))]
    codes = [
        "L1", "L2", "L3",
        "L6", "L7", "L8",
        "U2", "U3", "U4",
        "U9", "U9",
    ]
    hand = hand_from(codes, melds)
    # 暗手 11 张 + win_tile 1 张 = 12 张 = 3 组件 + 1 对将
    assert can_win(hand)  # 已是 11 张听牌？不，11 张要 12 张才算
    # 修：标准胡型需 4 组件 + 1 将；副露已占 1，暗手需 3 组件 + 1 将
    # 3 组件 = 9 张，1 对 = 2 张，合计 11 张暗手就能胡（不需要 win_tile，自摸理论上）
    # 但实际游戏胡牌时摸进了第 14 张，所以本应 win_tile=None 也成立
    # 实际测试：暗手就是 11 张，已经成型


def test_jiao_in_win():
    # 包含一个绞牌：L9 L9 U9
    codes = [
        "L1", "L2", "L3",
        "L4", "L5", "L6",
        "L9", "L9", "U9",  # 绞牌
        "U2", "U3", "U4",
        "U7", "U7",  # 将
    ]
    hand = hand_from(codes)
    assert can_win(hand)


def test_special_2_7_10_jvhua_win():
    # 「二七十」一句话也算
    codes = [
        "L2", "L7", "L10",  # 特殊句话
        "L1", "L2", "L3",
        "U4", "U5", "U6",
        "U7", "U8", "U9",
        "L5", "L5",  # 将
    ]
    hand = hand_from(codes)
    assert can_win(hand)


def test_xiao_qi_dui():
    codes = [
        "L1", "L1",
        "L3", "L3",
        "L5", "L5",
        "L7", "L7",
        "U2", "U2",
        "U6", "U6",
        "U9", "U9",
    ]
    hand = hand_from(codes)
    assert check_xiao_qi_dui(hand)


def test_shuang_long():
    codes = [
        "L1", "L1", "L1", "L1",  # 提
        "U5", "U5", "U5", "U5",  # 提
        "L3", "L3",
        "U7", "U7",
        "L9", "L9",
    ]
    hand = hand_from(codes)
    assert check_shuang_long(hand)


def test_no_win_garbage():
    codes = [
        "L1", "L3", "L5", "L7", "L9",
        "U2", "U4", "U6", "U8", "U10",
        "L2", "L4", "L6",
    ]
    hand = hand_from(codes)
    assert not can_win(hand, Tile("L", 8))


def test_tenpai_returns_waits():
    # 听 L4：1 2 3 + 5 6 7 + 8 9 10 + U1 U2 U3 + U5 U5 = 14
    # 缺 1 张同字号成将 → 不对，14 张已是胡
    # 改：13 张听 1 张
    codes = [
        "L1", "L2", "L3",
        "L5", "L6", "L7",
        "L8", "L9", "L10",
        "U1", "U2", "U3",
        "U5",  # 单张，等 U5 成将
    ]
    hand = hand_from(codes)
    waits = waiting_tiles(hand)
    assert Tile("U", 5) in waits
