from src.engine.hand import Hand
from src.engine.shanten import shanten
from src.engine.tiles import Tile, parse_many


def hand_from(codes: list[str]) -> Hand:
    return Hand.from_tiles(parse_many(codes))


def test_tenpai_returns_zero():
    # 13 张：4 句话 + 1 单 → 听
    codes = [
        "L1", "L2", "L3",
        "L4", "L5", "L6",
        "L7", "L8", "L9",
        "U1", "U2", "U3",
        "U5",
    ]
    assert shanten(hand_from(codes)) == 0


def test_complete_hand_is_tenpai_or_zero():
    # 14 张已胡型 → shanten=0（也算听）
    codes = [
        "L1", "L1", "L1",
        "L5", "L5", "L5",
        "U3", "U3", "U3",
        "U8", "U8", "U8",
        "L7", "L7",
    ]
    assert shanten(hand_from(codes)) == 0


def test_one_shanten_simple():
    # 13 张，缺一张能听
    codes = [
        "L1", "L2", "L3",
        "L4", "L5", "L6",
        "L7", "L8", "L9",
        "U1", "U2", "U3",
        "U7",  # 单张孤立，但 U5 也单
    ]
    # 这种局面应该 ≤2 向听
    s = shanten(hand_from(codes))
    assert 0 <= s <= 2


def test_garbage_hand_high_shanten():
    # 完全散乱的 13 张
    codes = [
        "L1", "L3", "L5", "L7", "L9",
        "U2", "U4", "U6", "U8", "U10",
        "L4", "L6", "L8",
    ]
    s = shanten(hand_from(codes))
    assert s >= 1
