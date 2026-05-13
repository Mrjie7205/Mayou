"""模板标注器（批量模式）。

用法：
    python -m tools.template_annotator                # 批量模式（默认）
    python -m tools.template_annotator <platform>     # 指定平台名
    python -m tools.template_annotator --single       # 单张模式（旧版）

批量模式流程：
1. 全屏遮罩，鼠标框选一片牌区（如一整排手牌、一片弃牌堆）
2. 弹出批量标注对话框：
   - 上方预览框选的整片图
   - 中部按等距切成 N 块，N 由 spinbox 调整（默认 14）
   - 每块下方一个输入框
3. 逐格输入字号（L1..L10 / U1..U10 / back，中文也行如 小七）
   留空的格不保存（用于被遮挡 / 不要的牌）
4. 点「保存所有」批量写到 assets/templates/<platform>/tiles/<kind>/
5. 关闭对话框后回到遮罩，继续下一次框选
6. Esc 退出

单张模式：框一张 → 弹输入框 → 保存 → 循环
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import mss
import numpy as np
from PySide6.QtCore import QPoint, QRect, Qt, QTimer
from PySide6.QtGui import QColor, QImage, QMouseEvent, QPainter, QPaintEvent, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
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


def _save_one(platform: str, kind: str, image_bgr: np.ndarray, suffix: str = "") -> Path:
    import cv2

    target_dir = TEMPLATES_DIR / platform / "tiles" / kind
    target_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    base = f"{ts}{('-' + suffix) if suffix else ''}"
    path = target_dir / f"{base}.png"
    i = 1
    while path.exists():
        path = target_dir / f"{base}-{i}.png"
        i += 1
    cv2.imwrite(str(path), image_bgr)
    return path


def _ndarray_to_qpixmap(image_bgr: np.ndarray, height: int | None = None) -> QPixmap:
    img = np.ascontiguousarray(image_bgr)
    h, w = img.shape[:2]
    qimg = QImage(
        img.data, w, h, img.strides[0],
        QImage.Format.Format_BGR888,
    ).copy()
    pix = QPixmap.fromImage(qimg)
    if height is not None and pix.height() > height:
        pix = pix.scaledToHeight(
            height,
            Qt.TransformationMode.SmoothTransformation,
        )
    return pix


class BatchAnnotateDialog(QDialog):
    def __init__(
        self,
        image_bgr: np.ndarray,
        platform: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.image_bgr = image_bgr
        self.platform = platform
        self._cell_inputs: list[QLineEdit] = []
        self._cell_widgets: list[QWidget] = []
        self._cell_images: list[np.ndarray] = []

        self.setWindowTitle("批量标注模板")
        self.resize(960, 600)

        outer = QVBoxLayout(self)

        # 顶部预览整片框选
        preview_label = QLabel()
        preview_pix = _ndarray_to_qpixmap(self.image_bgr, height=120)
        preview_label.setPixmap(preview_pix)
        preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(QLabel("框选区域预览："))
        outer.addWidget(preview_label)

        # 切块数调整
        ctrl = QHBoxLayout()
        ctrl.addWidget(QLabel("等距切成几块（按手牌张数选）："))
        self.spin = QSpinBox()
        self.spin.setRange(1, 20)
        self.spin.setValue(14)
        self.spin.valueChanged.connect(self._rebuild_cells)
        ctrl.addWidget(self.spin)
        ctrl.addStretch()
        outer.addLayout(ctrl)

        outer.addWidget(QLabel("每格下方输入字号（L1..L10 / U1..U10 / back / 中文如 小七）。留空不保存。"))

        # 切块网格容器
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setHorizontalSpacing(6)
        self.grid_layout.setVerticalSpacing(8)
        outer.addWidget(self.grid_container, 1)

        # 底部按钮
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        save_btn = QPushButton("保存所有标注")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(save_btn)
        outer.addLayout(btn_row)

        self._rebuild_cells()

    def _rebuild_cells(self) -> None:
        for w in self._cell_widgets:
            w.setParent(None)
            w.deleteLater()
        self._cell_widgets.clear()
        self._cell_inputs.clear()
        self._cell_images.clear()

        n = self.spin.value()
        h, w = self.image_bgr.shape[:2]
        cell_w = max(1, w // n)
        cols_per_row = 8

        for i in range(n):
            x_start = i * cell_w
            x_end = w if i == n - 1 else (i + 1) * cell_w
            cell_img = np.ascontiguousarray(self.image_bgr[:, x_start:x_end])
            self._cell_images.append(cell_img)

            wrapper = QWidget()
            cv = QVBoxLayout(wrapper)
            cv.setContentsMargins(2, 2, 2, 2)
            cv.setSpacing(4)

            thumb = QLabel()
            thumb_pix = _ndarray_to_qpixmap(cell_img, height=80)
            thumb.setPixmap(thumb_pix)
            thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
            thumb.setStyleSheet("background: #1e1e1e; border: 1px solid #555;")
            cv.addWidget(thumb)

            idx_label = QLabel(f"#{i + 1}")
            idx_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            idx_label.setStyleSheet("color: #888; font-size: 10px;")
            cv.addWidget(idx_label)

            edit = QLineEdit()
            edit.setPlaceholderText("如 L7")
            edit.setMaximumWidth(80)
            edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cv.addWidget(edit)

            self._cell_widgets.append(wrapper)
            self._cell_inputs.append(edit)

            row = i // cols_per_row
            col = i % cols_per_row
            self.grid_layout.addWidget(wrapper, row, col)

        if self._cell_inputs:
            self._cell_inputs[0].setFocus()

    def _on_save(self) -> None:
        saved = 0
        failed = []
        for i, edit in enumerate(self._cell_inputs):
            text = edit.text().strip()
            if not text:
                continue
            try:
                kind = _resolve_kind(text)
            except Exception as e:
                failed.append((i + 1, text, str(e)))
                continue
            _save_one(self.platform, kind, self._cell_images[i], suffix=f"i{i}")
            saved += 1

        if failed:
            details = "\n".join(
                f"  #{idx} = {txt!r} ({err})" for idx, txt, err in failed
            )
            QMessageBox.warning(
                self,
                "部分标签解析失败",
                f"已保存 {saved} 张，{len(failed)} 张失败：\n{details}",
            )
        else:
            QMessageBox.information(
                self, "保存完成", f"成功保存 {saved} 张模板到 {self.platform}",
            )
        self.accept()


class TemplateAnnotator(QWidget):
    def __init__(self, platform: str, batch_mode: bool = True) -> None:
        super().__init__()
        self.platform = platform
        self.batch_mode = batch_mode
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
        QTimer.singleShot(120, lambda: self._capture_and_handle(rect))

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            QApplication.quit()

    def _capture_and_handle(self, rect: QRect) -> None:
        with mss.mss() as sct:
            monitor = {
                "left": rect.x(),
                "top": rect.y(),
                "width": rect.width(),
                "height": rect.height(),
            }
            raw = sct.grab(monitor)
            image_bgr = np.ascontiguousarray(np.array(raw)[:, :, :3])

        if self.batch_mode:
            dlg = BatchAnnotateDialog(image_bgr, self.platform)
            dlg.exec()
        else:
            self._handle_single(image_bgr)

        self._start = None
        self._end = None
        self.show()
        self.update()

    def _handle_single(self, image_bgr: np.ndarray) -> None:
        text, ok = QInputDialog.getText(
            None,
            "标注模板",
            "输入这张牌（如 L7 / U10 / back / 小七 / 大拾 / 背面）：",
        )
        if not ok or not text:
            return
        try:
            kind = _resolve_kind(text)
            path = _save_one(self.platform, kind, image_bgr)
            QMessageBox.information(
                None, "已保存",
                f"模板 [{kind}] 写入 {path}",
            )
        except Exception as e:
            QMessageBox.warning(None, "保存失败", str(e))


def main() -> int:
    args = sys.argv[1:]
    batch_mode = True
    platform = "redfinger"
    for a in args:
        if a == "--single":
            batch_mode = False
        elif not a.startswith("-"):
            platform = a
    app = QApplication(sys.argv)
    annotator = TemplateAnnotator(platform, batch_mode=batch_mode)
    annotator.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
