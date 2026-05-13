"""屏幕区域框选工具。

启动后弹出半透明全屏遮罩，鼠标按下-拖动-松开框选一个矩形。
框选完成后弹出输入框让用户命名该区域，写入 assets/configs/redfinger.json
的 regions 字段。

支持**连续框多个区域**：每次命名保存后会自动回到遮罩，继续框下一个。
按 Esc 退出。

典型用法：
    python -m tools.region_picker
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PySide6.QtCore import QPoint, QRect, Qt, QTimer
from PySide6.QtGui import (
    QColor,
    QKeySequence,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QPen,
    QShortcut,
)
from PySide6.QtWidgets import (
    QApplication,
    QInputDialog,
    QMessageBox,
    QWidget,
)


CONFIG_PATH = (
    Path(__file__).resolve().parent.parent
    / "assets"
    / "configs"
    / "redfinger.json"
)


def _device_pixel_ratio() -> float:
    screen = QApplication.primaryScreen()
    if screen is None:
        return 1.0
    return float(screen.devicePixelRatio())


class RegionPicker(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.CrossCursor)
        screen_geo = QApplication.primaryScreen().virtualGeometry()
        self.setGeometry(screen_geo)
        self._start: QPoint | None = None
        self._end: QPoint | None = None

        # 全局 Esc 退出（不依赖窗口焦点）
        self._esc_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        self._esc_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self._esc_shortcut.activated.connect(QApplication.quit)

    def showEvent(self, event):
        super().showEvent(event)
        self.activateWindow()
        self.raise_()
        self.setFocus()

    def paintEvent(self, _event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 120))
        if self._start and self._end:
            rect = QRect(self._start, self._end).normalized()
            painter.setCompositionMode(
                QPainter.CompositionMode.CompositionMode_Clear
            )
            painter.fillRect(rect, Qt.GlobalColor.transparent)
            painter.setCompositionMode(
                QPainter.CompositionMode.CompositionMode_SourceOver
            )
            pen = QPen(QColor(255, 80, 80), 2)
            painter.setPen(pen)
            painter.drawRect(rect)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self._start = event.position().toPoint()
        self._end = self._start
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._start is None:
            return
        self._end = event.position().toPoint()
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self._start is None:
            return
        self._end = event.position().toPoint()
        rect = QRect(self._start, self._end).normalized()
        if rect.width() < 5 or rect.height() < 5:
            self._start = None
            self._end = None
            self.update()
            return
        self.hide()
        QTimer.singleShot(120, lambda: self._after_pick(rect))

    def _after_pick(self, rect: QRect) -> None:
        self._save_region(rect)
        self._start = None
        self._end = None
        self.show()
        self.update()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            QApplication.quit()

    def _save_region(self, rect: QRect) -> None:
        name, ok = QInputDialog.getText(
            None,
            "区域命名",
            "请输入区域名（如 my_hand / discard_self / meld_left / baojing_indicator）。\n"
            "取消则丢弃本次框选；保存后会回到遮罩继续框下一个，按 Esc 退出。",
        )
        if not ok or not name:
            return
        # 把 Qt 逻辑像素坐标转成物理像素（给 mss 用）
        ratio = _device_pixel_ratio()
        physical = {
            "x": int(round(rect.x() * ratio)),
            "y": int(round(rect.y() * ratio)),
            "w": int(round(rect.width() * ratio)),
            "h": int(round(rect.height() * ratio)),
        }
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        config: dict = {}
        if CONFIG_PATH.exists():
            try:
                config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                config = {}
        config.setdefault("platform", "redfinger")
        config.setdefault("regions", {})
        config["regions"][name.strip()] = physical
        CONFIG_PATH.write_text(
            json.dumps(config, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        QMessageBox.information(
            None,
            "已保存",
            f"区域 [{name}] 写入 {CONFIG_PATH.name}\n"
            f"物理像素 x={physical['x']} y={physical['y']} "
            f"w={physical['w']} h={physical['h']} (DPI ratio={ratio:.2f})",
        )


def main() -> int:
    app = QApplication(sys.argv)
    picker = RegionPicker()
    picker.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
