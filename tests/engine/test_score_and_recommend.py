import random
from collections import Counter

from src.engine.defense import OpponentInfo, evaluate_defense, is_genbutsu, is_jin
from src.engine.hand import Hand
from src.engine.recommend import recommend
from src.engine.score import (
    SOURCE_DIANPAO,
    SOURCE_SELF_DRAW,
    WinScore,
    estimate_win_kind,
)
from src.engine.tiles import Tile, parse_many


def test_score_normal_self_draw():
    s = WinScore.for_normal_win("normal", SOURCE_SELF_DRAW)
    assert s.base_score == 4
    assert s.total_received == 12


def test_score_pao_dianpao():
    s = WinScore.for_normal_win("pao_hu", SOURCE_DIANPAO)
    assert s.base_score == 24
    assert s.total_received == 24


def test_estimate_win_kind_normal():
    hand = Hand.from_tiles([])
    assert estimate_win_kind(hand) == "normal"


def test_genbutsu():
    opp = OpponentInfo(discards=[Tile("L", 5), Tile("U", 9)])
    assert is_genbutsu(Tile("L", 5), opp)
    assert not is_genbutsu(Tile("L", 6), opp)


def test_jin_basic():
    opp = OpponentInfo(discards=[Tile("L", 5)])
    # L2 因为 num=2 硬拦截，不算筋（Gemini 评审）
    assert not is_jin(Tile("L", 2), opp)
    # L8 仍算筋
    assert is_jin(Tile("L", 8), opp)
    assert not is_jin(Tile("L", 3), opp)


def test_defense_genbutsu_is_safest():
    opp = OpponentInfo(discards=[Tile("L", 5)])
    score = evaluate_defense(
        Tile("L", 5),
        {"across": opp},
        Counter(),
    )
    assert score.safety == 1.0


def test_recommend_returns_sorted():
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
        "across": OpponentInfo(discards=[Tile("U", 5), Tile("L", 6)]),
        "right": OpponentInfo(discards=[]),
    }
    recs = recommend(
        hand,
        opponents,
        all_visible=Counter(),
        simulations=50,
        rng=random.Random(42),
    )
    assert len(recs) > 0
    # 降序
    for i in range(len(recs) - 1):
        assert recs[i].combined >= recs[i + 1].combined
    # 排名连续
    assert [r.rank for r in recs] == list(range(1, len(recs) + 1))
