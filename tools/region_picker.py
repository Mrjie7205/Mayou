"""屏幕区域框选工具。

启动后弹出半透明全屏遮罩，鼠标按下-拖动-松开框选一个矩形。
框选完成后弹出输入框让用户命名该区域，写入 assets/configs/redfinger.json
的 regions 字段。

典型用法（Sprint 0/1 校准每个识别区域时反复运行）：
    python -m tools.region_picker

按 Esc 取消。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPaintEvent, QPen
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
        # virtualGeometry 覆盖所有显示器（多屏支持）
        screen_geo = QApplication.primaryScreen().virtualGeometry()
        self.setGeometry(screen_geo)
        self._start: QPoint | None = None
        self._end: QPoint | None = None

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
        self.update()
        self.hide()
        rect = QRect(self._start, self._end).normalized()
        if rect.width() < 5 or rect.height() < 5:
            QMessageBox.warning(None, "区域太小", "拖动太短，已取消保存。")
            QApplication.quit()
            return
        self._save_region(rect)
        QApplication.quit()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            QApplication.quit()

    def _save_region(self, rect: QRect) -> None:
        name, ok = QInputDialog.getText(
            None,
            "区域命名",
            "请输入区域名（如 my_hand / discard_self / meld_left / baojing_indicator）：",
        )
        if not ok or not name:
            return
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        config: dict = {}
        if CONFIG_PATH.exists():
            try:
                config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                config = {}
        config.setdefault("platform", "redfinger")
        config.setdefault("regions", {})
        config["regions"][name] = {
            "x": rect.x(),
            "y": rect.y(),
            "w": rect.width(),
            "h": rect.height(),
        }
        CONFIG_PATH.write_text(
            json.dumps(config, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        QMessageBox.information(
            None,
            "已保存",
            f"区域 [{name}] 写入 {CONFIG_PATH.name}\n"
            f"x={rect.x()} y={rect.y()} w={rect.width()} h={rect.height()}",
        )


def main() -> int:
    app = QApplication(sys.argv)
    picker = RegionPicker()
    picker.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
