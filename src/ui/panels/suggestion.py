"""出牌指引面板：候选牌完整 EV 排行表。

展示每张可打牌的净 EV 及其进攻/防守分项，便于调参时横向对比：
    排名 / 牌 / 净EV / 我胡期望 / 放炮预期 / 胡概率% / 安全度 / 打后向听

数据全来自 recommend() 返回的 Recommendation（已按 EV 降序），
本面板只做展示，不重复计算。
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QGroupBox,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.engine.recommend import Recommendation


# 列标题（短，适配窄面板）
_COLUMNS = ["#", "牌", "净EV", "我胡", "放炮", "胡率", "安全", "听"]

# 配色
_RED = QColor("#e57373")
_DEFAULT = QColor("#e0e0e0")
_EV_POS = QColor("#9ccc65")     # 正 EV 绿
_EV_NEG = QColor("#ef5350")     # 负 EV 红
_SHANTEN_GOOD = QColor("#9ccc65")  # 打后听牌（0）
_SHANTEN_BAD = QColor("#ffb74d")   # 打后向听升高
_ROW_HIGHLIGHT = QColor("#4a3f1e")  # #1 行底色（暗金）


class SuggestionPanel(QGroupBox):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("出牌指引", parent)

        self._placeholder = QLabel("（等待我的回合）")
        self._placeholder.setStyleSheet("color: #9e9e9e; padding: 6px;")

        self._table = QTableWidget(0, len(_COLUMNS))
        self._table.setHorizontalHeaderLabels(_COLUMNS)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionMode(QAbstractItemView.NoSelection)
        self._table.setFocusPolicy(Qt.NoFocus)
        self._table.setShowGrid(False)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet("font-size: 11px;")
        # 列宽：# 窄、牌 略宽、其余均分
        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        for i in range(2, len(_COLUMNS)):
            hdr.setSectionResizeMode(i, QHeaderView.Stretch)
        self._table.verticalHeader().setDefaultSectionSize(20)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addWidget(self._placeholder)
        layout.addWidget(self._table)

    def update_recommendations(self, recs: list[Recommendation]) -> None:
        if not recs:
            self._placeholder.setText("（手里没牌可打）")
            self._placeholder.show()
            self._table.hide()
            self._table.setRowCount(0)
            return

        self._placeholder.hide()
        self._table.show()
        self._table.setRowCount(len(recs))

        for row, rec in enumerate(recs):
            is_top = row == 0
            self._set_cell(row, 0, str(rec.rank), _DEFAULT, is_top, Qt.AlignCenter)
            self._set_cell(
                row, 1, rec.tile.display_name + (" (红)" if rec.tile.is_red else ""),
                _RED if rec.tile.is_red else _DEFAULT, is_top, Qt.AlignCenter,
            )
            ev_color = _EV_POS if rec.ev >= 0 else _EV_NEG
            self._set_cell(row, 2, f"{rec.ev:+.1f}", ev_color, is_top, Qt.AlignCenter)
            self._set_cell(row, 3, f"{rec.ev_my:.1f}", _DEFAULT, is_top, Qt.AlignCenter)
            self._set_cell(row, 4, f"{rec.ev_loss:.1f}", _DEFAULT, is_top, Qt.AlignCenter)
            self._set_cell(
                row, 5, f"{rec.attack.win_prob * 100:.0f}%",
                _DEFAULT, is_top, Qt.AlignCenter,
            )
            self._set_cell(
                row, 6, f"{rec.defense.safety:.2f}", _DEFAULT, is_top, Qt.AlignCenter,
            )
            # 打后向听：0=听牌（好），越大越差
            sh = rec.attack.shanten_after
            sh_color = _SHANTEN_GOOD if sh == 0 else (
                _SHANTEN_BAD if sh >= 2 else _DEFAULT
            )
            self._set_cell(row, 7, str(sh), sh_color, is_top, Qt.AlignCenter)

    def _set_cell(
        self, row: int, col: int, text: str,
        color: QColor, bold: bool, align: Qt.Alignment,
    ) -> None:
        item = QTableWidgetItem(text)
        item.setTextAlignment(align)
        item.setForeground(color)
        if bold:
            f = item.font()
            f.setBold(True)
            item.setFont(f)
            item.setBackground(_ROW_HIGHLIGHT)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        self._table.setItem(row, col, item)
