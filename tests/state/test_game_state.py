from src.engine.tiles import Tile, parse_many
from src.state.events import Event
from src.state.game_state import GameState


def test_fresh_initial_state():
    gs = GameState.fresh(dealer="self")
    assert gs.dealer == "self"
    assert gs.current_turn == "self"
    assert gs.deck_remaining == 23
    assert not gs.finished


def test_deal_self_hand():
    gs = GameState.fresh()
    initial = parse_many(["L1", "L2", "L3", "L5", "L7"])
    gs.apply_event(Event(
        type="deal", seat="self",
        tiles=tuple(initial),
        extra={"dealer": "self"},
    ))
    assert gs.seats["self"].hand.closed_size() == 5


def test_draw_then_discard():
    gs = GameState.fresh()
    gs.apply_event(Event(
        type="deal", seat="self",
        tiles=tuple(parse_many(["L1", "L2", "L3"])),
    ))
    gs.apply_event(Event(type="draw", seat="self", tile=Tile("L", 5)))
    assert gs.seats["self"].hand.closed_size() == 4
    assert gs.deck_remaining == 22

    gs.apply_event(Event(type="discard", seat="self", tile=Tile("L", 5)))
    assert gs.seats["self"].hand.closed_size() == 3
    assert Tile("L", 5) in gs.seats["self"].discards


def test_opponent_discard_tracked():
    gs = GameState.fresh()
    gs.apply_event(Event(type="discard", seat="left", tile=Tile("U", 7)))
    assert Tile("U", 7) in gs.seats["left"].discards


def test_peng_increments_count():
    gs = GameState.fresh()
    gs.apply_event(Event(
        type="deal", seat="self",
        tiles=tuple(parse_many(["L5", "L5"])),
    ))
    gs.apply_event(Event(type="peng", seat="self", tile=Tile("L", 5)))
    assert gs.seats["self"].peng_count == 1
    assert gs.seats["self"].hand.closed_size() == 0
    assert any(m.type == "peng" for m in gs.seats["self"].hand.melds)


def test_baojing():
    gs = GameState.fresh()
    gs.apply_event(Event(type="baojing", seat="across"))
    assert gs.seats["across"].is_baojing


def test_hu_marks_winner_finishes_game():
    gs = GameState.fresh()
    gs.apply_event(Event(type="hu", seat="self"))
    assert gs.seats["self"].is_winner
    assert gs.finished


def test_remaining_kind_count():
    gs = GameState.fresh()
    gs.apply_event(Event(
        type="deal", seat="self",
        tiles=tuple(parse_many(["L5"])),
    ))
    gs.apply_event(Event(type="discard", seat="left", tile=Tile("L", 5)))
    assert gs.remaining_kind_count(Tile("L", 5)) == 2
    assert gs.remaining_kind_count(Tile("U", 9)) == 4
