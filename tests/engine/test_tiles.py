from src.engine.tiles import (
    ALL_KINDS,
    DECK_COUNT_PER_KIND,
    TOTAL_TILES,
    Tile,
    full_deck,
    parse,
)


def test_total_count():
    assert len(ALL_KINDS) == 20
    assert TOTAL_TILES == 80
    assert len(full_deck()) == 80


def test_red_classification():
    assert Tile("L", 2).is_red
    assert Tile("L", 7).is_red
    assert Tile("L", 10).is_red
    assert Tile("U", 2).is_red
    assert Tile("U", 7).is_red
    assert Tile("U", 10).is_red
    assert not Tile("L", 1).is_red
    assert not Tile("L", 5).is_red
    assert not Tile("U", 9).is_red


def test_display_names():
    assert Tile("L", 1).display_name == "小一"
    assert Tile("L", 7).display_name == "小七"
    assert Tile("U", 2).display_name == "大贰"
    assert Tile("U", 10).display_name == "大拾"


def test_parse_codes_and_chinese():
    assert parse("L7") == Tile("L", 7)
    assert parse("U10") == Tile("U", 10)
    assert parse("小七") == Tile("L", 7)
    assert parse("大壹") == Tile("U", 1)
    assert parse("大拾") == Tile("U", 10)


def test_ordering():
    assert Tile("L", 1) < Tile("L", 2)
    assert Tile("L", 10) < Tile("U", 1)
