"""shanten 测试（基于 5 门子模型）。"""
from src.engine.hand import Hand
from src.engine.shanten import shanten
from src.engine.tiles import parse_many


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
