"""Mayou 主入口。

Sprint 0：启动 PySide6 主控台窗口 + 200ms 心跳 timer。
后续 Sprint 接入：截图 → 识别 → 状态机 → 引擎 → UI 更新。

本地运行：
    python -m src.main
"""
import sys

from PySide6.QtWidgets import QApplication

from src.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Mayou")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
