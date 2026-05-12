from src.engine.tiles import Tile
from src.recognize.template_loader import (
    template_kind_to_tile,
    template_summary,
    tile_to_template_kind,
)


def test_kind_to_tile_lower():
    assert template_kind_to_tile("lower_7") == Tile("L", 7)


def test_kind_to_tile_upper():
    assert template_kind_to_tile("upper_10") == Tile("U", 10)


def test_kind_to_tile_back():
    assert template_kind_to_tile("back") is None


def test_tile_to_kind_roundtrip():
    for tile in [Tile("L", 1), Tile("L", 10), Tile("U", 5), Tile("U", 10)]:
        assert template_kind_to_tile(tile_to_template_kind(tile)) == tile


def test_template_summary_empty():
    summary = template_summary("nonexistent_platform_xyz")
    assert summary == {}


def test_kind_to_tile_invalid_raises():
    import pytest
    with pytest.raises(ValueError):
        template_kind_to_tile("garbage")
