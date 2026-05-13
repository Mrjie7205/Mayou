"""记牌器面板：20 字号 × 大小写 × 红黑 × 剩余张数。"""
from __future__ import annotations

from collections import Counter

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from src.engine.tiles import LOWER_NAMES, UPPER_NAMES, Tile


class CounterPanel(QGroupBox):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("记牌器", parent)
        self._cells: dict[Tile, QLabel] = {}
        outer = QVBoxLayout(self)
        outer.addWidget(self._make_section("小写", "L", LOWER_NAMES))
        outer.addWidget(self._make_section("大写", "U", UPPER_NAMES))
        outer.addStretch()

    def _make_section(self, title: str, case: str, names: list[str]) -> QWidget:
        wrap = QWidget()
        v = QVBoxLayout(wrap)
        v.setContentsMargins(0, 0, 0, 0)
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("color: #888;")
        v.addWidget(title_lbl)
        grid = QGridLayout()
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(2)
        v.addLayout(grid)
        for n in range(1, 11):
            tile = Tile(case, n)
            cell = QLabel(self._format(tile, 4))
            cell.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cell.setStyleSheet(self._cell_style(tile, 4))
            grid.addWidget(cell, (n - 1) // 5, (n - 1) % 5)
            self._cells[tile] = cell
        return wrap

    def update_remaining(self, counter: Counter) -> None:
        for tile, label in self._cells.items():
            count = counter.get(tile, 0)
            label.setText(self._format(tile, count))
            label.setStyleSheet(self._cell_style(tile, count))

    @staticmethod
    def _format(tile: Tile, count: int) -> str:
        red_dot = "🔴" if tile.is_red else ""
        return f"{tile.display_name[1]} {count}{red_dot}"

    @staticmethod
    def _cell_style(tile: Tile, count: int) -> str:
        if count == 0:
            color = "#9e9e9e"
        elif count == 1:
            color = "#ffd54f"
        elif tile.is_red:
            color = "#ff6b6b"
        else:
            color = "#f5f5f5"
        weight = "bold" if count <= 1 or tile.is_red else "normal"
        return (
            f"color: {color}; font-size: 13px; "
            f"font-weight: {weight}; padding: 3px 6px;"
        )
