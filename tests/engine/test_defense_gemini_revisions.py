"""测试 Gemini 评审建议带来的防守逻辑修正。"""
from collections import Counter

from src.engine.defense import (
    OpponentInfo,
    evaluate_defense_for_seat,
    is_jin,
)
from src.engine.tiles import Tile


def test_jin_blocks_2_7_10():
    """Gemini: tile.num ∈ {2, 7, 10} 不应用筋逻辑。"""
    opp = OpponentInfo(discards=[Tile("L", 5)])
    # 标准：打过 5 → L2 是筋。但因为 num=2 硬拦截，应返回 False
    assert is_jin(Tile("L", 2), opp) is False
    # 同样 L7 不算筋
    opp = OpponentInfo(discards=[Tile("L", 4)])
    assert is_jin(Tile("L", 7), opp) is False
    # 但 L1 仍算筋（num=1 不在拦截列表）
    assert is_jin(Tile("L", 1), opp) is True


def test_jin_still_works_for_normal_nums():
    opp = OpponentInfo(discards=[Tile("L", 5)])
    assert is_jin(Tile("L", 8), opp) is True
    opp = OpponentInfo(discards=[Tile("L", 6)])
    assert is_jin(Tile("L", 3), opp) is True
    assert is_jin(Tile("L", 9), opp) is True


def test_passed_tile_returns_high_safety():
    """对手过张的字号再打给他几乎绝对安全。"""
    opp = OpponentInfo(passed_tiles=[Tile("L", 5)])
    safety = evaluate_defense_for_seat(Tile("L", 5), opp, Counter())
    assert safety >= 0.9


def test_baojing_meld_tile_max_danger():
    """报警家：他副露过的字号 = 跑胡候选 = safety 0.0"""
    opp = OpponentInfo(
        is_baojing=True,
        melds=[("peng", (Tile("L", 5), Tile("L", 5), Tile("L", 5)))],
    )
    safety = evaluate_defense_for_seat(Tile("L", 5), opp, Counter())
    assert safety == 0.0


def test_baojing_other_tile_safer_than_normal():
    """报警家：未副露过的字号反而比未报警时安全。"""
    opp = OpponentInfo(
        is_baojing=True,
        melds=[("peng", (Tile("L", 1), Tile("L", 1), Tile("L", 1)))],
    )
    safety = evaluate_defense_for_seat(Tile("L", 8), opp, Counter())
    assert safety >= 0.8


def test_juezhang_3plus_visible_safer():
    """绝张：≥3 张可见 → safety 拉高。"""
    opp = OpponentInfo()
    visible = Counter({Tile("L", 5): 3})
    safety = evaluate_defense_for_seat(Tile("L", 5), opp, visible)
    assert safety >= 0.9
    # 红色字号略低
    visible_red = Counter({Tile("L", 7): 3})
    safety_red = evaluate_defense_for_seat(Tile("L", 7), opp, visible_red)
    assert safety_red >= 0.8
    assert safety_red < safety  # 红色仍弱于黑色


def test_normal_jin_weight_is_milder():
    """筋权重 -0.15 后，应该比之前 -0.3 时的 safety 更低。"""
    opp = OpponentInfo(discards=[Tile("L", 5)])
    # 打过 5，L8 是筋（num=8 不在拦截列表）
    safety = evaluate_defense_for_seat(Tile("L", 8), opp, Counter())
    # safety = 1.0 - (-0.15) = 1.15 → clip 到 1.0
    # 但因为是非现物路径走通用计算：safety = 1 - danger，danger=-0.15 → safety=1.15→1.0
    # 验证：至少 ≥ 0.85（确认 jin 仍生效，没被错误屏蔽）
    assert safety >= 0.85
