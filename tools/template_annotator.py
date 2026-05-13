"""模板标注器：从屏幕上选一张牌的图块 → 输入字号 → 存为 PNG。

用法：
    python -m tools.template_annotator              # 默认 platform=redfinger
    python -m tools.template_annotator <platform>

启动后流程：
1. 弹出全屏半透明遮罩
2. 鼠标拖框选一张牌（在云手机窗口里）
3. 松开 → 隐藏遮罩 → 截图框选区域 → 弹输入框
4. 输入 kind 代码：L1..L10 / U1..U10 / back 中文也行：小七、大壹、背面
5. 自动存到 assets/templates/<platform>/tiles/<kind>/<时间戳>.png
6. 重新弹出遮罩，继续下一张（按 Esc 退出）
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import mss
import numpy as np
from PySide6.QtCore import QPoint, QRect, Qt, QTimer
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import (
    QApplication,
    QInputDialog,
    QMessageBox,
    QWidget,
)

from src.engine.tiles import parse
from src.recognize.template_loader import (
    TEMPLATES_DIR,
    tile_to_template_kind,
)


def _resolve_kind(user_input: str) -> str:
    s = user_input.strip()
    if s in ("back", "背面"):
        return "back"
    tile = parse(s)
    return tile_to_template_kind(tile)


def _save_image(platform: str, kind: str, image_bgr: np.ndarray) -> Path:
    import cv2

    target_dir = TEMPLATES_DIR / platform / "tiles" / kind
    target_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    fname = f"{ts}.png"
    i = 1
    while (target_dir / fname).exists():
        fname = f"{ts}-{i}.png"
        i += 1
    path = target_dir / fname
    cv2.imwrite(str(path), image_bgr)
    return path


class TemplateAnnotator(QWidget):
    def __init__(self, platform: str) -> None:
        super().__init__()
        self.platform = platform
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
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))
        if self._start and self._end:
            rect = QRect(self._start, self._end).normalized()
            painter.setCompositionMode(
                QPainter.CompositionMode.CompositionMode_Clear
            )
            painter.fillRect(rect, Qt.GlobalColor.transparent)
            painter.setCompositionMode(
                QPainter.CompositionMode.CompositionMode_SourceOver
            )
            pen = QPen(QColor(80, 200, 80), 2)
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
        if rect.width() < 8 or rect.height() < 8:
            self._start = None
            self._end = None
            self.update()
            return
        self.hide()
        QTimer.singleShot(120, lambda: self._capture_and_save(rect))

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            QApplication.quit()

    def _capture_and_save(self, rect: QRect) -> None:
        with mss.mss() as sct:
            monitor = {
                "left": rect.x(),
                "top": rect.y(),
                "width": rect.width(),
                "height": rect.height(),
            }
            raw = sct.grab(monitor)
            image_bgr = np.ascontiguousarray(np.array(raw)[:, :, :3])

        text, ok = QInputDialog.getText(
            None,
            "标注模板",
            "输入这张牌（如 L7 / U10 / back / 小七 / 大拾 / 背面）：",
        )
        if ok and text:
            try:
                kind = _resolve_kind(text)
                path = _save_image(self.platform, kind, image_bgr)
                QMessageBox.information(
                    None,
                    "已保存",
                    f"模板 [{kind}] 写入 {path.relative_to(Path.cwd())}",
                )
            except Exception as e:
                QMessageBox.warning(None, "保存失败", str(e))

        self._start = None
        self._end = None
        self.show()
        self.update()


def main() -> int:
    platform = sys.argv[1] if len(sys.argv) > 1 else "redfinger"
    app = QApplication(sys.argv)
    annotator = TemplateAnnotator(platform)
    annotator.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
