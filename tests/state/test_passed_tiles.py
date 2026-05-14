"""测试过张事件能更新 SeatState.passed_tiles。"""
from src.engine.tiles import Tile
from src.state.events import Event
from src.state.game_state import GameState


def test_guo_zhang_records_to_seat():
    gs = GameState.fresh()
    gs.apply_event(Event(type="guo_zhang", seat="left", tile=Tile("L", 5)))
    assert Tile("L", 5) in gs.seats["left"].passed_tiles


def test_guo_zhang_dedupes():
    gs = GameState.fresh()
    gs.apply_event(Event(type="guo_zhang", seat="across", tile=Tile("U", 7)))
    gs.apply_event(Event(type="guo_zhang", seat="across", tile=Tile("U", 7)))
    assert gs.seats["across"].passed_tiles.count(Tile("U", 7)) == 1


def test_guo_zhang_per_seat():
    gs = GameState.fresh()
    gs.apply_event(Event(type="guo_zhang", seat="left", tile=Tile("L", 5)))
    gs.apply_event(Event(type="guo_zhang", seat="right", tile=Tile("L", 5)))
    assert Tile("L", 5) in gs.seats["left"].passed_tiles
    assert Tile("L", 5) in gs.seats["right"].passed_tiles
    assert Tile("L", 5) not in gs.seats["across"].passed_tiles
