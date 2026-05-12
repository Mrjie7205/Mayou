"""演示模式：用预设事件序列驱动整个 UI。

启动 `python -m src.main --demo` 后，DemoDriver 按时间表把模拟事件
喂给 GameState，整个 UI 看起来像真实一局正在进行。

事件序列设计为约 60 秒一局，覆盖：发牌 / 摸打 / 碰 / 五福报警 / 胡。
"""
from __future__ import annotations

from PySide6.QtCore import QDateTime, QObject, QTimer, Signal

from src.engine.tiles import Tile, parse_many
from src.state.events import Event
from src.state.game_state import GameState


def make_demo_events() -> list[Event]:
    """返回带 t 字段的事件列表。"""
    initial_hand = parse_many([
        "L1", "L2", "L3", "L5", "L5",
        "L7", "L8", "U1", "U2", "U3",
        "U5", "U6", "U7", "U9",
    ])
    raw: list[tuple[float, Event]] = [
        (0.0, Event(
            type="deal", seat="self",
            tiles=tuple(initial_hand),
            extra={"dealer": "self"},
        )),
        (3.0, Event(type="draw", seat="self", tile=Tile("L", 6))),
        (6.5, Event(type="discard", seat="self", tile=Tile("U", 9))),
        (9.5, Event(type="draw", seat="left")),
        (11.5, Event(type="discard", seat="left", tile=Tile("L", 10))),
        (14.0, Event(type="draw", seat="across")),
        (16.0, Event(type="discard", seat="across", tile=Tile("U", 4))),
        (18.5, Event(type="draw", seat="right")),
        (20.5, Event(type="discard", seat="right", tile=Tile("L", 4))),
        (23.0, Event(type="draw", seat="self", tile=Tile("U", 8))),
        (26.0, Event(type="discard", seat="self", tile=Tile("U", 1))),
        (28.5, Event(
            type="peng", seat="across", tile=Tile("U", 1),
            note="对家碰自己刚打的 U1",
        )),
        (31.0, Event(type="discard", seat="across", tile=Tile("L", 9))),
        (33.5, Event(type="draw", seat="right")),
        (35.5, Event(type="discard", seat="right", tile=Tile("U", 6))),
        (38.0, Event(type="draw", seat="self", tile=Tile("U", 4))),
        (41.0, Event(type="discard", seat="self", tile=Tile("L", 7))),
        (43.5, Event(type="draw", seat="left")),
        (45.5, Event(type="discard", seat="left", tile=Tile("L", 5))),
        (48.0, Event(
            type="baojing", seat="across",
            note="演示：对家完成 4 碰，触发五福报警",
        )),
        (50.5, Event(type="draw", seat="right")),
        (52.5, Event(type="discard", seat="right", tile=Tile("L", 6))),
        (55.0, Event(
            type="hu", seat="self", tile=Tile("L", 5),
            note="演示：自己自摸 L5 胡",
        )),
    ]
    out = []
    for t, ev in raw:
        ev.t = t
        out.append(ev)
    return out


class DemoDriver(QObject):
    state_changed = Signal()

    def __init__(self, gs: GameState, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.gs = gs
        self.events = make_demo_events()
        self._idx = 0
        self._start_ms = 0
        self._paused = False
        self._pause_offset = 0
        self._pause_started_at = 0
        self._timer = QTimer(self)
        self._timer.setInterval(150)
        self._timer.timeout.connect(self._tick)

    def start(self) -> None:
        self._start_ms = QDateTime.currentMSecsSinceEpoch()
        self._idx = 0
        self._pause_offset = 0
        self._timer.start()

    def set_paused(self, paused: bool) -> None:
        if paused == self._paused:
            return
        if paused:
            self._pause_started_at = QDateTime.currentMSecsSinceEpoch()
        else:
            self._pause_offset += (
                QDateTime.currentMSecsSinceEpoch() - self._pause_started_at
            )
        self._paused = paused

    def _elapsed_seconds(self) -> float:
        return (
            QDateTime.currentMSecsSinceEpoch()
            - self._start_ms
            - self._pause_offset
        ) / 1000.0

    def _tick(self) -> None:
        if self._paused or self._idx >= len(self.events):
            return
        elapsed = self._elapsed_seconds()
        progressed = False
        while (
            self._idx < len(self.events)
            and self.events[self._idx].t <= elapsed
        ):
            ev = self.events[self._idx]
            self.gs.apply_event(ev)
            self._idx += 1
            progressed = True
        if progressed:
            self.state_changed.emit()
