"""Mayou 主控台主窗口。

布局：
- 左半：屏幕区域适配（占位）+ 当前局势（占位）
- 右半：出牌指引 / 记牌器 / 牌局分析 / 事件日志（均占位）
- 顶栏：暂停 / 设置
- 暂停热键：Ctrl+Space

Sprint 0 阶段：只搭骨架，所有面板内容是占位文本。
"""
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QMainWindow):
    paused_changed = Signal(bool)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Mayou - 株洲碰胡辅助")
        self.resize(1100, 800)
        self.setMinimumSize(900, 600)
        self._paused = False
        self._tick = 0

        self._build_ui()
        self._setup_shortcuts()
        self._start_demo_timer()
        self._set_status("启动完成。请按左侧指引把红手指窗口拖到屏幕左半。")

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        left_col = QVBoxLayout()
        left_col.addWidget(self._build_capture_panel(), 3)
        left_col.addWidget(self._build_situation_panel(), 2)

        right_col = QVBoxLayout()
        right_col.addWidget(self._build_suggestion_panel(), 2)
        right_col.addWidget(self._build_counter_panel(), 3)
        right_col.addWidget(self._build_analysis_panel(), 2)
        right_col.addWidget(self._build_event_log_panel(), 3)

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
        settings_btn = QPushButton("⚙ 设置")
        settings_btn.clicked.connect(self._open_settings)
        tb.addWidget(settings_btn)

    def _build_capture_panel(self) -> QWidget:
        box = QGroupBox("屏幕区域适配")
        layout = QVBoxLayout(box)
        placeholder = QLabel(
            "🎯 把红手指 PC 客户端拖到屏幕左半边\n"
            "    目标尺寸 1280 × 720（Sprint 0 实测后修订）\n\n"
            "（适配区占位 · 后续 Sprint 填充截图预览与识别框）"
        )
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
        placeholder.setMinimumHeight(300)
        layout.addWidget(placeholder)

        btn_row = QHBoxLayout()
        btn_row.addWidget(QPushButton("抓帧预览"))
        btn_row.addWidget(QPushButton("保存适配"))
        btn_row.addStretch()
        layout.addLayout(btn_row)
        return box

    def _build_situation_panel(self) -> QWidget:
        box = QGroupBox("当前局势")
        layout = QVBoxLayout(box)
        layout.addWidget(QLabel("（向听 / 等待张 / 胡概率 / 期望积分 占位）"))
        return box

    def _build_suggestion_panel(self) -> QWidget:
        box = QGroupBox("出牌指引")
        layout = QVBoxLayout(box)
        layout.addWidget(QLabel("（推荐 + 备选 共 2 张 占位）"))
        return box

    def _build_counter_panel(self) -> QWidget:
        box = QGroupBox("记牌器")
        layout = QVBoxLayout(box)
        layout.addWidget(
            QLabel("（20 种字 × 大小写 × 红黑分组 占位）")
        )
        return box

    def _build_analysis_panel(self) -> QWidget:
        box = QGroupBox("牌局分析")
        layout = QVBoxLayout(box)
        layout.addWidget(QLabel("（上家/对家/下家危险度 + 五福报警 占位）"))
        return box

    def _build_event_log_panel(self) -> QWidget:
        box = QGroupBox("事件日志")
        layout = QVBoxLayout(box)
        self._event_label = QLabel("（最近 20 条事件占位）")
        layout.addWidget(self._event_label)
        return box

    def _setup_shortcuts(self) -> None:
        QShortcut(QKeySequence("Ctrl+Space"), self, self._toggle_pause)

    def _start_demo_timer(self) -> None:
        # Sprint 0 验证：每 200ms 触发一次 "tick"，更新状态栏作为存活信号。
        # 后续 Sprint 替换为真正的主循环（截图 → 识别 → 状态 → 引擎）。
        self._timer = QTimer(self)
        self._timer.setInterval(200)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start()

    def _on_tick(self) -> None:
        if self._paused:
            return
        self._tick += 1
        self._set_status(f"心跳 #{self._tick}（每 200ms · Sprint 0 占位）")

    def _toggle_pause(self) -> None:
        self._paused = not self._paused
        if self._paused:
            self._pause_btn.setText("⏸ 已暂停（Ctrl+Space 恢复）")
            self._set_status("已暂停。")
        else:
            self._pause_btn.setText("▶ 抓帧中（Ctrl+Space 暂停）")
            self._set_status("抓帧继续。")
        self.paused_changed.emit(self._paused)

    def _open_settings(self) -> None:
        self._set_status("⚙ 设置面板待后续 Sprint 实现")

    def _set_status(self, text: str) -> None:
        self.statusBar().showMessage(text)
