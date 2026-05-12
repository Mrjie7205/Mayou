"""Demo 模式不依赖 Qt 的端到端冒烟测试。

验证 demo 事件序列能完整应用到 GameState 而不崩，且最终结束。
"""
from src.state.game_state import GameState
from src.ui.demo_mode import make_demo_events


def test_demo_events_applies_cleanly():
    gs = GameState.fresh()
    events = make_demo_events()
    assert len(events) > 10
    for ev in events:
        gs.apply_event(ev)
    assert gs.finished
    assert any(s.is_winner for s in gs.seats.values())


def test_demo_events_have_monotonic_timestamps():
    events = make_demo_events()
    times = [e.t for e in events]
    assert times == sorted(times)
    assert times[0] == 0.0


def test_demo_includes_baojing_and_hu():
    types = {e.type for e in make_demo_events()}
    assert "deal" in types
    assert "discard" in types
    assert "peng" in types
    assert "baojing" in types
    assert "hu" in types
