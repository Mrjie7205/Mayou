"""事件日志面板：最近 N 条事件，最新在上。"""
from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QGroupBox,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.state.events import Event


SEAT_DISPLAY = {
    "self": "自己",
    "left": "上家",
    "across": "对家",
    "right": "下家",
}

TYPE_DISPLAY = {
    "deal": "发牌",
    "draw": "摸",
    "discard": "打",
    "peng": "碰",
    "wei": "偎(强制)",
    "ti": "提",
    "pao": "跑",
    "chi": "吃",
    "ren": "忍",
    "guo_zhang": "过张",
    "baojing": "五福报警",
    "hu": "胡",
    "chou_zhuang": "臭庄",
}


class EventLogPanel(QGroupBox):
    def __init__(self, parent: QWidget | None = None, max_items: int = 30) -> None:
        super().__init__("事件日志", parent)
        self.max_items = max_items
        self._list = QListWidget()
        self._list.setStyleSheet(
            "QListWidget { background: #1e1e1e; color: #c0c0c0; "
            "font-family: monospace; font-size: 11px; }"
        )
        layout = QVBoxLayout(self)
        layout.addWidget(self._list)

    def append_event(self, event: Event) -> None:
        text = self._format(event)
        if event.confidence < 0.7:
            text = "⚠ " + text
        item = QListWidgetItem(text)
        if event.confidence < 0.7:
            item.setForeground(QColor("#ffa726"))
        elif event.type == "hu":
            item.setForeground(QColor("#80cbc4"))
        elif event.type == "baojing":
            item.setForeground(QColor("#ef5350"))
        self._list.insertItem(0, item)
        while self._list.count() > self.max_items:
            self._list.takeItem(self._list.count() - 1)

    def replace_all(self, events: list[Event]) -> None:
        self._list.clear()
        for ev in reversed(events[-self.max_items:]):
            self.append_event(ev)

    @staticmethod
    def _format(event: Event) -> str:
        seat = SEAT_DISPLAY.get(event.seat or "", "")
        type_ = TYPE_DISPLAY.get(event.type, event.type)
        tile_str = event.tile.display_name if event.tile else ""
        prefix = f"[{event.t:6.1f}s]"
        if seat and tile_str:
            return f"{prefix} {seat} {type_} {tile_str}"
        if seat:
            return f"{prefix} {seat} {type_}"
        return f"{prefix} {type_} {tile_str}"
