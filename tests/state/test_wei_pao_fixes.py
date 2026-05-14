"""审计后修复的 game_state bug 测试。"""
from collections import Counter

from src.engine.hand import Hand, Meld
from src.engine.tiles import Tile, parse_many
from src.state.events import Event
from src.state.game_state import GameState


def hand_from(codes):
    return Hand.from_tiles(parse_many(codes))


def test_wei_deducts_three_tiles_from_closed():
    """self 偎：draw 已 add 1 张 → wei 应扣 3 张（原对 2 + 新摸 1）。"""
    gs = GameState.fresh()
    # 起手手里有 L5×2
    gs.apply_event(Event(
        type="deal", seat="self",
        tiles=tuple(parse_many(["L5", "L5", "L1", "L2"])),
    ))
    # 摸 L5 → closed[L5]=3
    gs.apply_event(Event(type="draw", seat="self", tile=Tile("L", 5)))
    assert gs.seats["self"].hand.closed.get(Tile("L", 5), 0) == 3

    # 偎 L5 → closed 应清空 L5（扣 3 张）
    gs.apply_event(Event(type="wei", seat="self", tile=Tile("L", 5)))
    assert gs.seats["self"].hand.closed.get(Tile("L", 5), 0) == 0
    # meld 中 wei 组应有 3 张 L5
    melds = gs.seats["self"].hand.melds
    assert any(m.type == "wei" and m.tiles == (Tile("L", 5),) * 3 for m in melds)


def test_pao_self_draws_tile_extracts_from_closed():
    """场景 (a)：自摸到已碰过的字号 → 跑 → 扣 1 张 closed。"""
    gs = GameState.fresh()
    # 假设已碰过 L5
    gs.seats["self"].hand.melds.append(
        Meld("peng", (Tile("L", 5),) * 3)
    )
    # 起手少量手牌（与碰无关）
    gs.seats["self"].hand.closed = Counter({Tile("L", 1): 1})

    # 摸 L5 → closed[L5]=1
    gs.apply_event(Event(type="draw", seat="self", tile=Tile("L", 5)))
    assert gs.seats["self"].hand.closed.get(Tile("L", 5), 0) == 1

    # 跑 L5 → closed 清空 L5；peng 升级为 ti
    gs.apply_event(Event(type="pao", seat="self", tile=Tile("L", 5)))
    assert gs.seats["self"].hand.closed.get(Tile("L", 5), 0) == 0
    melds = gs.seats["self"].hand.melds
    assert any(m.type == "ti" and m.tiles == (Tile("L", 5),) * 4 for m in melds)
    assert not any(m.type == "peng" for m in melds)


def test_pao_external_trigger_does_not_touch_closed():
    """场景 (b)：别人打的牌是自己已碰的 → closed 不动。"""
    gs = GameState.fresh()
    gs.seats["self"].hand.melds.append(
        Meld("peng", (Tile("L", 5),) * 3)
    )
    gs.seats["self"].hand.closed = Counter({Tile("L", 1): 1})

    # 跑事件触发，但 closed 没有 L5（外部触发）
    before = dict(gs.seats["self"].hand.closed)
    gs.apply_event(Event(type="pao", seat="self", tile=Tile("L", 5)))
    after = dict(gs.seats["self"].hand.closed)
    assert before == after


def test_pao_for_opponent_seat_never_touches_closed():
    """对手跑：他没暗手数据，跑只更新 meld。"""
    gs = GameState.fresh()
    gs.seats["across"].hand.melds.append(
        Meld("peng", (Tile("U", 9),) * 3)
    )
    gs.apply_event(Event(type="pao", seat="across", tile=Tile("U", 9)))
    melds = gs.seats["across"].hand.melds
    assert any(m.type == "ti" for m in melds)
