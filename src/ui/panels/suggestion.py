"""出牌指引面板：显示 #1 推荐 + #2 备选。"""
from __future__ import annotations

from PySide6.QtWidgets import QGroupBox, QLabel, QVBoxLayout, QWidget

from src.engine.recommend import Recommendation


class SuggestionPanel(QGroupBox):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("出牌指引", parent)
        self._top_label = QLabel("（等待引擎计算）")
        self._top_label.setStyleSheet(
            "color: #ffd54f; font-size: 14px; font-weight: bold;"
        )
        self._top_label.setWordWrap(True)
        self._second_label = QLabel("")
        self._second_label.setStyleSheet("color: #c0c0c0;")
        self._second_label.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.addWidget(self._top_label)
        layout.addWidget(self._second_label)
        layout.addStretch()

    def update_recommendations(self, recs: list[Recommendation]) -> None:
        if not recs:
            self._top_label.setText("（手里没牌可打）")
            self._second_label.setText("")
            return
        first = recs[0]
        self._top_label.setText(self._format(first, label="#1 推荐"))
        if len(recs) >= 2:
            self._second_label.setText(self._format(recs[1], label="#2 备选"))
        else:
            self._second_label.setText("")

    @staticmethod
    def _format(rec: Recommendation, label: str) -> str:
        red_mark = " (红)" if rec.tile.is_red else ""
        return (
            f"{label}: {rec.tile.display_name}{red_mark}\n"
            f"  进攻 {rec.attack.composite:.2f}（胡 {rec.attack.win_prob*100:.0f}% / 期望 {rec.attack.expected_score:.1f} 分）\n"
            f"  防守 {rec.defense.safety:.2f}\n"
            f"  综合 {rec.combined:.2f}"
        )
