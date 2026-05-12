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

from src.engine.tiles import LOWER_NAMES, RED_NUMBERS, UPPER_NAMES, Tile


class CounterPanel(QGroupBox):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("记牌器", parent)
        outer = QVBoxLayout(self)

        outer.addWidget(self._make_section("小写", "L", LOWER_NAMES))
        outer.addWidget(self._make_section("大写", "U", UPPER_NAMES))
        outer.addStretch()

        self._cells: dict[Tile, QLabel] = {}
        self._build_cells()

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
        wrap._grid = grid  # type: ignore[attr-defined]
        wrap._case = case  # type: ignore[attr-defined]
        wrap._names = names  # type: ignore[attr-defined]
        return wrap

    def _build_cells(self) -> None:
        # 小写 grid 和大写 grid 都已挂在 layout 上；这里向各自 grid 填 cells
        # 直接遍历内部子 widget 找出对应 grid
        sections = []
        layout = self.layout()
        for i in range(layout.count()):
            w = layout.itemAt(i).widget()
            if w is not None and hasattr(w, "_grid"):
                sections.append(w)
        for section in sections:
            grid = section._grid  # type: ignore[attr-defined]
            case = section._case  # type: ignore[attr-defined]
            names = section._names  # type: ignore[attr-defined]
            for n in range(1, 11):
                tile = Tile(case, n)
                cell = QLabel(self._format(tile, 4))
                cell.setAlignment(Qt.AlignmentFlag.AlignCenter)
                cell.setStyleSheet(self._cell_style(tile, 4))
                grid.addWidget(cell, (n - 1) // 5, (n - 1) % 5)
                self._cells[tile] = cell

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
        color = "#e57373" if tile.is_red else "#e0e0e0"
        if count == 0:
            color = "#555"
        elif count == 1:
            color = "#ffd54f"
        weight = "bold" if count <= 1 else "normal"
        return f"color: {color}; font-weight: {weight}; padding: 2px 4px;"
