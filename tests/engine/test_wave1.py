"""Wave 1 单测（ADR-003）：对手向听粗估 / 卡位 / MC 启发式 / EV 公式。"""
import random
from collections import Counter

from src.engine.defense import (
    OpponentInfo,
    estimate_opponent_shanten,
    evaluate_defense_for_seat,
)
from src.engine.hand import Hand, Meld
from src.engine.monte_carlo import _fast_eval_discard
from src.engine.recommend import (
    estimate_loss_per_seat,
    estimate_opp_win_prob_factor,
    recommend,
)
from src.engine.tiles import Tile, parse_many


# ---- Wave 1.2: 对手向听粗估 ----

def test_shanten_estimate_baojing_is_1():
    opp = OpponentInfo(is_baojing=True)
    assert estimate_opponent_shanten(opp) == 1


def test_shanten_estimate_three_melds():
    opp = OpponentInfo(
        melds=[("peng", (Tile("L", 1),) * 3)] * 3,
    )
    assert estimate_opponent_shanten(opp) == 1


def test_shanten_estimate_no_info():
    opp = OpponentInfo()
    assert estimate_opponent_shanten(opp) >= 4


def test_shanten_estimate_many_discards():
    opp = OpponentInfo(discards=[Tile("L", i) for i in range(1, 10)])
    assert estimate_opponent_shanten(opp) <= 3


# ---- Wave 1.4: 卡位防守 ----

def test_kawei_three_peng_uninvisible_high_danger():
    opp = OpponentInfo(
        peng_count=3,
        melds=[("peng", (Tile("L", 1),) * 3)] * 3,
    )
    visible = Counter({Tile("L", 1): 3})
    # 未现身字号（visible_count == 0）应触发卡位
    safety = evaluate_defense_for_seat(Tile("U", 5), opp, visible)
    assert safety < 0.4


def test_kawei_does_not_apply_when_baojing():
    # 已报警时走 baojing 分支，卡位逻辑不触发
    opp = OpponentInfo(
        is_baojing=True,
        peng_count=4,
        melds=[("peng", (Tile("L", 1),) * 3)] * 4,
    )
    safety = evaluate_defense_for_seat(Tile("U", 5), opp, Counter({Tile("L", 1): 3}))
    # 报警家未副露字号 → 0.85（不是卡位的 0.2）
    assert safety >= 0.7


# ---- Wave 1.3: MC 启发式弃牌 ----

def test_fast_eval_prefers_isolated_tiles():
    # 手里：L1 单张 + 一对 L5 + 一对 L7（红）
    closed = Counter({Tile("L", 1): 1, Tile("L", 5): 2, Tile("L", 7): 2})
    rng = random.Random(42)
    # 跑 50 次，孤张 L1 应该是被选最多的
    picks = [_fast_eval_discard(closed, rng) for _ in range(50)]
    most = max(set(picks), key=picks.count)
    assert most == Tile("L", 1)


def test_fast_eval_forbidden_respected():
    closed = Counter({Tile("L", 5): 2, Tile("L", 1): 1})
    rng = random.Random(7)
    for _ in range(10):
        pick = _fast_eval_discard(closed, rng, forbidden=Tile("L", 5))
        assert pick != Tile("L", 5)


def test_fast_eval_avoids_red_tile():
    closed = Counter({Tile("L", 1): 1, Tile("L", 2): 1})  # L2 红色
    rng = random.Random(99)
    picks = [_fast_eval_discard(closed, rng) for _ in range(50)]
    # L1 比 L2 更常被打（红色保留偏向）
    n_l1 = picks.count(Tile("L", 1))
    n_l2 = picks.count(Tile("L", 2))
    assert n_l1 > n_l2


# ---- Wave 1.1: EV 公式 ----

def test_loss_per_seat_baojing_largest():
    normal = estimate_loss_per_seat(OpponentInfo())
    baojing = estimate_loss_per_seat(OpponentInfo(is_baojing=True))
    assert baojing > normal


def test_opp_win_factor_decreases_with_shanten():
    high_threat = estimate_opp_win_prob_factor(OpponentInfo(is_baojing=True))
    low_threat = estimate_opp_win_prob_factor(OpponentInfo())
    assert high_threat > low_threat


def test_recommend_sorts_by_ev():
    codes = [
        "L1", "L2", "L3",
        "L5", "L6", "L7",
        "L9", "L9", "L9",
        "U2", "U2",
        "U7", "U8",
    ]
    hand = Hand.from_tiles(parse_many(codes))
    opponents = {
        "left": OpponentInfo(discards=[Tile("L", 1)]),
        "across": OpponentInfo(
            is_baojing=True,
            melds=[("peng", (Tile("L", 5),) * 3)],
        ),
        "right": OpponentInfo(),
    }
    recs = recommend(
        hand, opponents, all_visible=Counter(),
        simulations=30, rng=random.Random(1),
    )
    assert len(recs) > 0
    # 严格按 EV 降序
    for i in range(len(recs) - 1):
        assert recs[i].ev >= recs[i + 1].ev
    # 第一名 EV 应 ≥ 第二名（基本健康检查）
    assert recs[0].rank == 1


def test_recommend_baojing_opponent_drives_high_loss():
    """对家报警时，给他放炮的字号 EV 应该明显低于其他。"""
    codes = ["L1", "L2", "L3", "L5", "L6", "L7", "L9", "L9", "L9",
             "U2", "U2", "U7", "U8"]
    hand = Hand.from_tiles(parse_many(codes))
    danger_tile = Tile("U", 7)  # 假设对家碰过 U7
    opponents = {
        "left": OpponentInfo(),
        "across": OpponentInfo(
            is_baojing=True,
            melds=[("peng", (danger_tile,) * 3)],
        ),
        "right": OpponentInfo(),
    }
    recs = recommend(
        hand, opponents, all_visible=Counter(),
        simulations=30, rng=random.Random(2),
    )
    by_tile = {r.tile: r for r in recs}
    # 包含 U7 时（用户手里有），ev_loss 应该有非零失分
    if danger_tile in by_tile:
        assert by_tile[danger_tile].ev_loss > 0
