"""字牌胡型测试（5 门子 + 15 张 + k=m 约束）。

合法 (k, m, j) 组合：
    (0, 0, 5)：5 个 3 张组件
    (1, 1, 3)：1 对 + 1 提 + 3 个 3 张
    (2, 2, 1)：2 对 + 2 提 + 1 个 3 张
"""
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


def hand_from(codes, melds=None):
    return Hand.from_tiles(parse_many(codes), melds or [])


# ===== (k=0, m=0, j=5)：5 个 3 张组件，无对无提 =====

def test_five_jvhua_no_pair_no_ti():
    """5 个句话连续胡：庄家典型 15 张胡型。"""
    codes = [
        "L1", "L2", "L3",
        "L4", "L5", "L6",
        "L7", "L8", "L9",
        "U1", "U2", "U3",
        "U5", "U6", "U7",
    ]
    assert standard_can_win(hand_from(codes))


def test_five_kan():
    """5 个坎（5 个 3 张）= 15 张胡。"""
    codes = [
        "L1", "L1", "L1",
        "L5", "L5", "L5",
        "U3", "U3", "U3",
        "U8", "U8", "U8",
        "L7", "L7", "L7",
    ]
    assert standard_can_win(hand_from(codes))


def test_jiao_jvhua_kan_mix():
    """绞牌 + 句话 + 坎 混合 5 个 3 张组件。"""
    codes = [
        "L1", "L2", "L3",         # 句话
        "L4", "L5", "L6",         # 句话
        "L9", "L9", "U9",         # 绞牌
        "U2", "U3", "U4",         # 句话
        "U7", "U7", "U7",         # 坎
    ]
    assert standard_can_win(hand_from(codes))


def test_special_2_7_10_jvhua_in_5menzi():
    """二七十特殊句话作为门子之一。"""
    codes = [
        "L2", "L7", "L10",        # 特殊句话
        "L1", "L2", "L3",         # 句话
        "U4", "U5", "U6",         # 句话
        "U7", "U8", "U9",         # 句话
        "L5", "L5", "L5",         # 坎
    ]
    assert standard_can_win(hand_from(codes))


# ===== (k=1, m=1, j=3)：1 对 + 1 提 + 3 个 3 张 =====

def test_1_pair_1_ti_3_three_components():
    """像刘艺杰那局胡型：1 对 + 1 提 + 3 个 3 张 = 15 张。"""
    codes = [
        "L6", "L6", "L6", "L6",   # 提 4 张
        "L8", "L8", "U8",         # 绞牌
        "U6", "U7", "U8",         # 句话
        "U4", "U5", "U6",         # 句话
        "U10", "U10",             # 对
    ]
    assert standard_can_win(hand_from(codes))


def test_with_ti_meld_and_pair_in_closed():
    """副露含 1 提 + 暗手凑 (k=1, m=0)：满足 k_an=1, m_an=0, meld_ti=1 → k=m=1 全局 OK"""
    melds = [Meld("ti", (Tile("L", 6),) * 4)]  # 1 提副露
    codes = [
        "L1", "L2", "L3",         # 句话
        "U4", "U5", "U6",         # 句话
        "U7", "U8", "U9",         # 句话
        "U10", "U10",             # 对（暗手对，对应 k_an=1）
    ]
    # 副露 4 张 + 暗手 11 张 = 15 ✓
    # meld_ti=1, k_an=1, m_an=0, j_an=3 → 暗手张数 2+0+9=11 ✓
    assert standard_can_win(hand_from(codes, melds))


# ===== (k=2, m=2, j=1)：2 对 + 2 提 + 1 个 3 张 =====

def test_2_pair_2_ti_1_three():
    """罕见胡型：2 对 + 2 提 + 1 个 3 张 = 4+8+3 = 15 张。"""
    codes = [
        "L1", "L1", "L1", "L1",   # 提
        "U1", "U1", "U1", "U1",   # 提
        "L5", "L6", "L7",         # 句话
        "L10", "L10",             # 对
        "U10", "U10",             # 对
    ]
    assert standard_can_win(hand_from(codes))


# ===== 违反 k=m 约束的牌型不能胡 =====

def test_14_tile_4_jvhua_1_pair_rejected():
    """14 张 4 个 3 张 + 1 对（违反 k=m=0 但 k=1）→ 不胡。"""
    codes = [
        "L1", "L2", "L3",
        "L4", "L5", "L6",
        "U1", "U2", "U3",
        "U5", "U6", "U7",
        "L9", "L9",
    ]
    assert not standard_can_win(hand_from(codes))


def test_4_kan_1_pair_violates_km():
    """4 坎 + 1 对 = 14 张违反 k=m。"""
    codes = [
        "L1", "L1", "L1",
        "L5", "L5", "L5",
        "U3", "U3", "U3",
        "U8", "U8", "U8",
        "L7", "L7",
    ]
    assert not standard_can_win(hand_from(codes))


# ===== 副露场景 =====

def test_three_melds_plus_two_three_in_closed():
    """3 个副露 + 2 个 3 张暗手组件 = 5 门子。"""
    melds = [
        Meld("peng", (Tile("L", 5),) * 3),
        Meld("an_ke", (Tile("U", 3),) * 3),
        Meld("chi_jvhua", (Tile("U", 7), Tile("U", 8), Tile("U", 9))),
    ]
    # 副露 9 张，目标暗手 6 张 = 2 个 3 张组件
    codes = [
        "L1", "L2", "L3",
        "U1", "U2", "U3",
    ]
    assert standard_can_win(hand_from(codes, melds))


def test_four_melds_with_ti_plus_pair():
    """4 副露含 1 提 + 暗手大拾对（刘艺杰最后一局胡型）。"""
    melds = [
        Meld("ti", (Tile("L", 6),) * 4),
        Meld("chi_jiao", (Tile("L", 8), Tile("L", 8), Tile("U", 8))),
        Meld("chi_jvhua", (Tile("U", 6), Tile("U", 7), Tile("U", 8))),
        Meld("chi_jvhua", (Tile("U", 4), Tile("U", 5), Tile("U", 6))),
    ]
    # 副露 4+3+3+3 = 13 张, meld_ti=1
    # 目标 target = 15-13 = 2，暗手 2 张
    # k=m 全局：k_total = m_total → k_an = m_an + meld_ti = m_an + 1
    # k_an=1, m_an=0, j_an = 5-4-1-0 = 0 → 张数 2+0+0=2 ✓
    codes = ["U10", "U10"]
    assert standard_can_win(hand_from(codes, melds))


# ===== 特殊起手胡型 =====

def test_xiao_qi_dui():
    """小七对：14 张 7 对（唯一 14 张胡型）。"""
    codes = [
        "L1", "L1",
        "L3", "L3",
        "L5", "L5",
        "L7", "L7",
        "U2", "U2",
        "U6", "U6",
        "U9", "U9",
    ]
    assert check_xiao_qi_dui(hand_from(codes))
    assert can_win(hand_from(codes))


def test_shuang_long():
    """双龙：起手 2 个一提（不受 5 门子约束）。"""
    codes = [
        "L1", "L1", "L1", "L1",
        "U5", "U5", "U5", "U5",
        "L3", "L3",
        "U7", "U7",
        "L9", "L9",
        "L2",
    ]
    assert check_shuang_long(hand_from(codes))


# ===== 散牌不胡 =====

def test_garbage_hand_no_win():
    codes = [
        "L1", "L3", "L5", "L7", "L9",
        "U2", "U4", "U6", "U8", "U10",
        "L2", "L4", "L6", "L8", "L10",
    ]
    # 15 张但完全凑不出 5 门子结构
    assert not standard_can_win(hand_from(codes))


# ===== 听张枚举 =====

def test_tenpai_waiting_one_tile_for_kan():
    """14 张听 1 张（差 1 张大伍升坎成第 5 个门子）。

    副露 3 组 + 暗手 大伍×2 + 1 个完整组件 = 4 副露 + 半门子（大伍×2）
    => 14 张 → 听大伍 1 张
    """
    melds = [
        Meld("an_ke", (Tile("L", 6),) * 3),
        Meld("chi_jvhua", (Tile("U", 1), Tile("U", 2), Tile("U", 3))),
        Meld("chi_jvhua", (Tile("U", 4), Tile("U", 5), Tile("U", 6))),
        Meld("chi_jvhua", (Tile("U", 7), Tile("U", 8), Tile("U", 9))),
    ]
    # 副露 12 张, 目标 target = 15-12 = 3 张暗手
    # 暗手 = 大伍×2 + 1 个其他散张？要凑 1 个完整 3 张组件
    # 实际：摸大伍 → 大伍×3 坎 = 第 5 个门子
    # 暗手有大伍×2，听 1 张大伍
    codes = ["U5", "U5"]
    hand = hand_from(codes, melds)
    # 此时 14 张（12+2），不能直接胡。摸大伍 → 15 张 = 胡型
    waits = waiting_tiles(hand)
    assert Tile("U", 5) in waits
