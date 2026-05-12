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


def main() -> int:
    parser = argparse.ArgumentParser(prog="mayou")
    parser.add_argument(
        "--demo", action="store_true",
        help="演示模式：用预设事件序列驱动 UI（不需要红手指）",
    )
    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setApplicationName("Mayou")

    gs = GameState.fresh(dealer="self")
    demo = DemoDriver(gs) if args.demo else None

    window = MainWindow(gs, demo_driver=demo)
    window.show()

    if demo is not None:
        demo.start()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
