"""当前局势面板：显示自己的核心数字 + 自己手牌的简要展示。"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from src.engine.tiles import Tile


class SituationPanel(QGroupBox):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("当前局势", parent)
        self._info = QLabel("等待发牌...")
        self._info.setStyleSheet("color: #80cbc4; font-weight: bold;")
        self._hand_label = QLabel("")
        self._hand_label.setWordWrap(True)
        self._hand_label.setStyleSheet(
            "background: #1e1e1e; padding: 6px; "
            "font-size: 14px; letter-spacing: 4px;"
        )
        layout = QVBoxLayout(self)
        layout.addWidget(self._info)
        layout.addWidget(QLabel("我的手牌："))
        layout.addWidget(self._hand_label)
        layout.addStretch()

    def update_info(self, shanten: int, deck_remaining: int, turn: str) -> None:
        seat_name = {
            "self": "自己", "left": "上家",
            "across": "对家", "right": "下家",
        }.get(turn, turn)
        head = "听牌" if shanten == 0 else f"{shanten} 向听"
        self._info.setText(
            f"{head} | 牌墩剩 {deck_remaining} 张 | 当前轮：{seat_name}"
        )

    def update_hand(self, tiles: list[Tile]) -> None:
        sorted_tiles = sorted(tiles, key=lambda t: (t.case, t.num))
        parts = []
        for t in sorted_tiles:
            color = "#e57373" if t.is_red else "#e0e0e0"
            parts.append(
                f'<span style="color: {color};">{t.display_name}</span>'
            )
        self._hand_label.setText("".join(parts))
