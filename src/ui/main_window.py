"""Mayou 主控台主窗口（按 docs/05 布局）。

左半：屏幕区域适配 + 当前局势
右半：出牌指引 + 记牌器 + 牌局分析 + 事件日志
顶栏：暂停/恢复（Ctrl+Space）+ 设置
"""
from __future__ import annotations

import random

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from src.engine.defense import OpponentInfo
from src.engine.recommend import recommend
from src.engine.shanten import shanten
from src.engine.win_check import waiting_tiles
from src.state.events import Event
from src.state.game_state import GameState
from src.ui.panels.analysis import AnalysisPanel
from src.ui.panels.capture import CapturePanel
from src.ui.panels.counter import CounterPanel
from src.ui.panels.event_log import EventLogPanel
from src.ui.panels.situation import SituationPanel
from src.ui.panels.suggestion import SuggestionPanel


class MainWindow(QMainWindow):
    def __init__(self, game_state: GameState, demo_driver=None) -> None:
        super().__init__()
        self.setWindowTitle("Mayou - 株洲碰胡辅助")
        self.resize(1200, 850)
        self.setMinimumSize(960, 640)
        self.gs = game_state
        self.demo = demo_driver
        self._paused = False
        self._rng = random.Random(20260512)
        self._last_event_idx = 0

        self._build_ui()
        self._setup_shortcuts()
        if self.demo is not None:
            self.demo.state_changed.connect(self._on_state_changed)
        self._on_state_changed()
        self._set_status(
            "运行中 · 演示模式" if demo_driver else "运行中 · 等待真实数据"
        )

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        self.capture_panel = CapturePanel()
        self.situation_panel = SituationPanel()
        self.suggestion_panel = SuggestionPanel()
        self.counter_panel = CounterPanel()
        self.analysis_panel = AnalysisPanel()
        self.event_log_panel = EventLogPanel()

        left_col = QVBoxLayout()
        left_col.addWidget(self.capture_panel, 3)
        left_col.addWidget(self.situation_panel, 2)

        right_col = QVBoxLayout()
        right_col.addWidget(self.suggestion_panel, 2)
        right_col.addWidget(self.counter_panel, 3)
        right_col.addWidget(self.analysis_panel, 2)
        right_col.addWidget(self.event_log_panel, 3)

        root.addLayout(left_col, 5)
        root.addLayout(right_col, 4)

        self._build_toolbar()
        self.setStatusBar(QStatusBar())

    def _build_toolbar(self) -> None:
        tb = QToolBar("main")
        tb.setMovable(False)
        self.addToolBar(tb)
        self._pause_btn = QPushButton("▶ 抓帧中（Ctrl+Space 暂停）")
        self._pause_btn.clicked.connect(self._toggle_pause)
        tb.addWidget(self._pause_btn)
        tb.addSeparator()
        self._settings_btn = QPushButton("⚙ 设置")
        self._settings_btn.clicked.connect(self._open_settings)
        tb.addWidget(self._settings_btn)

    def _setup_shortcuts(self) -> None:
        QShortcut(QKeySequence("Ctrl+Space"), self, self._toggle_pause)

    def _toggle_pause(self) -> None:
        self._paused = not self._paused
        if self.demo is not None:
            self.demo.set_paused(self._paused)
        if self._paused:
            self._pause_btn.setText("⏸ 已暂停（Ctrl+Space 恢复）")
            self._set_status("已暂停。")
        else:
            self._pause_btn.setText("▶ 抓帧中（Ctrl+Space 暂停）")
            self._set_status("继续。")

    def _open_settings(self) -> None:
        self._set_status("⚙ 设置面板待后续 Sprint 实现")

    def _set_status(self, text: str) -> None:
        self.statusBar().showMessage(text)

    def _on_state_changed(self) -> None:
        gs = self.gs
        my = gs.seats["self"]
        my_hand = my.hand

        sh = shanten(my_hand) if my_hand.closed_size() > 0 else 99
        self.situation_panel.update_info(sh, gs.deck_remaining, gs.current_turn)

        self.counter_panel.update_remaining(gs.remaining_counter())

        opponents = {
            seat: OpponentInfo(
                discards=list(s.discards),
                melds=[(m.type, m.tiles) for m in s.hand.melds],
                peng_count=s.peng_count,
                is_baojing=s.is_baojing,
                passed_tiles=list(s.passed_tiles),
            )
            for seat, s in gs.seats.items() if seat != "self"
        }

        self.analysis_panel.update_opponents(opponents)
        waits = (
            waiting_tiles(my_hand)
            if sh == 0 and my_hand.closed_size() > 0
            else []
        )

        last_event = gs.history[-1] if gs.history else None
        should_recommend = (
            last_event is not None
            and last_event.seat == "self"
            and last_event.type in ("draw", "deal")
            and not gs.finished
            and my_hand.closed_size() > 0
        )
        win_prob = 0.0
        expected = 0.0
        highlight = None
        if should_recommend:
            try:
                recs = recommend(
                    my_hand, opponents,
                    all_visible=gs.all_visible_tiles(),
                    simulations=80,
                    rng=self._rng,
                )
                self.suggestion_panel.update_recommendations(recs)
                if recs:
                    win_prob = recs[0].attack.win_prob
                    expected = recs[0].attack.expected_score
                    highlight = recs[0].tile
            except Exception as e:
                self._set_status(f"推荐计算失败：{e}")
        else:
            # 非自己回合：清掉陈旧建议，避免误导
            self.suggestion_panel.update_recommendations([])

        # 手牌渲染放在推荐之后，才能高亮 #1 推荐牌
        self.situation_panel.update_hand(
            list(my_hand.closed.elements()), highlight=highlight
        )
        self.analysis_panel.update_self(sh, waits, win_prob, expected)

        new_events = gs.history[self._last_event_idx:]
        for ev in new_events:
            self.event_log_panel.append_event(ev)
        self._last_event_idx = len(gs.history)

        if gs.finished:
            winner = next(
                (s.seat for s in gs.seats.values() if s.is_winner),
                None,
            )
            if winner:
                self._set_status(f"局结束：{winner} 胡")
