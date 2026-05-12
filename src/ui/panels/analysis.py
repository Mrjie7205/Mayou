"""牌局分析面板：自己向听 + 三家危险度。"""
from __future__ import annotations

from PySide6.QtWidgets import QGroupBox, QLabel, QVBoxLayout, QWidget

from src.engine.defense import OpponentInfo
from src.engine.tiles import Tile


class AnalysisPanel(QGroupBox):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("牌局分析", parent)
        self._self_label = QLabel("自己 - 向听 - / 等待 -")
        self._self_label.setStyleSheet("color: #80cbc4; font-weight: bold;")
        self._opp_labels = {
            "left": QLabel("上家 ⚪"),
            "across": QLabel("对家 ⚪"),
            "right": QLabel("下家 ⚪"),
        }
        layout = QVBoxLayout(self)
        layout.addWidget(self._self_label)
        for lbl in self._opp_labels.values():
            lbl.setWordWrap(True)
            layout.addWidget(lbl)
        layout.addStretch()

    def update_self(
        self,
        shanten: int,
        waiting: list[Tile],
        win_prob: float,
        expected_score: float,
    ) -> None:
        wait_str = (
            "、".join(t.display_name for t in waiting[:6])
            + (" ..." if len(waiting) > 6 else "")
        )
        if shanten == 0:
            head = f"自己 听牌 / 等 {wait_str}"
            tail = f"\n  胡概率 {win_prob*100:.0f}% / 期望 {expected_score:.1f} 分"
        else:
            head = f"自己 {shanten} 向听"
            tail = ""
        self._self_label.setText(head + tail)

    def update_opponents(self, opponents: dict[str, OpponentInfo]) -> None:
        for seat, opp in opponents.items():
            label = self._opp_labels.get(seat)
            if label is None:
                continue
            text, color = self._render_opp(seat, opp)
            label.setText(text)
            label.setStyleSheet(f"color: {color};")

    @staticmethod
    def _render_opp(seat: str, opp: OpponentInfo) -> tuple[str, str]:
        seat_name = {"left": "上家", "across": "对家", "right": "下家"}[seat]
        if opp.is_baojing:
            return (f"{seat_name} 🔴 五福报警！(只能胡五福或跑胡)", "#ef5350")
        if opp.peng_count >= 3:
            return (f"{seat_name} 🟡 已碰 {opp.peng_count} 次（接近报警）", "#ffb74d")
        if len(opp.discards) <= 2:
            return (f"{seat_name} ⚪ 弃牌 {len(opp.discards)} 张（信息不足）", "#9e9e9e")
        return (f"{seat_name} 🟢 弃 {len(opp.discards)}（现物多）", "#81c784")
