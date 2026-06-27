"""Mayou 主入口。

- python -m src.main           启动主控台（等待真实数据接入）
- python -m src.main --demo    启动演示模式（模拟一局）
"""
from __future__ import annotations

import argparse
import sys

from PySide6.QtWidgets import QApplication

from src.state.game_state import GameState
from src.ui.demo_mode import DemoDriver
from src.ui.main_window import MainWindow


DARK_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #2b2b2b;
    color: #e0e0e0;
}
QGroupBox {
    background-color: #2b2b2b;
    color: #e0e0e0;
    border: 1px solid #555;
    border-radius: 4px;
    margin-top: 14px;
    padding-top: 6px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    color: #80cbc4;
    font-weight: bold;
}
QLabel {
    color: #e0e0e0;
    background: transparent;
}
QPushButton {
    background-color: #424242;
    color: #e0e0e0;
    border: 1px solid #555;
    padding: 4px 14px;
    border-radius: 3px;
}
QPushButton:hover {
    background-color: #505050;
    border: 1px solid #777;
}
QPushButton:pressed {
    background-color: #353535;
}
QListWidget {
    background-color: #1e1e1e;
    color: #c0c0c0;
    border: 1px solid #444;
}
QTableWidget {
    background-color: #1e1e1e;
    color: #e0e0e0;
    border: 1px solid #444;
    gridline-color: #2b2b2b;
    selection-background-color: #3a4a5a;
}
QTableWidget::item {
    padding: 1px 2px;
}
QTableWidget::item:alternate {
    background-color: #242424;
}
QHeaderView::section {
    background-color: #353535;
    color: #80cbc4;
    padding: 3px;
    border: none;
    font-weight: bold;
}
QStatusBar {
    background-color: #2b2b2b;
    color: #80cbc4;
}
QToolBar {
    background-color: #353535;
    border: none;
    padding: 4px;
}
QInputDialog, QMessageBox {
    background-color: #2b2b2b;
    color: #e0e0e0;
}
QLineEdit {
    background-color: #1e1e1e;
    color: #e0e0e0;
    border: 1px solid #555;
    padding: 3px;
    border-radius: 2px;
}
"""


def main() -> int:
    parser = argparse.ArgumentParser(prog="mayou")
    parser.add_argument(
        "--demo", action="store_true",
        help="演示模式：用预设事件序列驱动 UI（不需要红手指）",
    )
    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setApplicationName("Mayou")
    app.setStyleSheet(DARK_STYLESHEET)

    gs = GameState.fresh(dealer="self")
    demo = DemoDriver(gs) if args.demo else None

    window = MainWindow(gs, demo_driver=demo)
    window.show()

    if demo is not None:
        demo.start()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
