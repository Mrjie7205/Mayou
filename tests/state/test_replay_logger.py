import json
from pathlib import Path

from src.engine.tiles import Tile
from src.state.events import Event
from src.state.replay_logger import ReplaySession


def test_replay_save(tmp_path: Path):
    session = ReplaySession(platform="test", dealer="self")
    session.append(Event(type="deal", seat="self", tile=Tile("L", 1), t=0.0))
    session.append(Event(type="discard", seat="left", tile=Tile("U", 5), t=2.5))
    session.finalize({"result": "hu", "winner": "self", "score": 18})
    path = session.save(tmp_path)
    assert path.exists()

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["session"]["platform"] == "test"
    assert data["session"]["dealer"] == "self"
    assert len(data["events"]) == 2
    assert data["events"][1]["type"] == "discard"
    assert data["events"][1]["tile"] == "U5"
    assert data["outcome"]["result"] == "hu"
