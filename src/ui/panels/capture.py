"""屏幕区域适配面板（Sprint 0 占位 + 简易抓帧预览）。

按 docs/05 §左半边：
- 显示一个虚线参考框 + 目标尺寸提示
- 「抓帧预览」按钮 → 调用 mss 截图屏幕左半 → 缩略图显示
- 「保存适配」按钮 → 写 redfinger.json 配置（占位）
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class CapturePanel(QGroupBox):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("屏幕区域适配", parent)

        self._preview = QLabel(
            "🎯 把红手指 PC 客户端拖到屏幕左半边\n"
            "    目标尺寸 1280 × 720（Sprint 0 实测后修订）\n\n"
            "（点 [抓帧预览] 测试截屏。\n"
            "  实际识别框叠加将在 Sprint 2 接入。）"
        )
        self._preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
        self._preview.setMinimumHeight(280)
        self._preview.setStyleSheet(
            "color: #888; background: #1e1e1e; border: 2px dashed #555;"
        )

        self._capture_btn = QPushButton("抓帧预览")
        self._capture_btn.clicked.connect(self._on_capture)
        self._save_btn = QPushButton("保存适配")
        self._save_btn.clicked.connect(self._on_save)

        layout = QVBoxLayout(self)
        layout.addWidget(self._preview, 1)
        btn_row = QHBoxLayout()
        btn_row.addWidget(self._capture_btn)
        btn_row.addWidget(self._save_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

    def _on_capture(self) -> None:
        try:
            from src.capture.screen_grab import grab_primary_screen
            img = grab_primary_screen()
            h, w = img.shape[:2]
            half_w = w // 2
            half = img[:, :half_w]
            qimg = QImage(
                half.data, half_w, h, half.strides[0],
                QImage.Format.Format_BGR888,
            ).copy()
            pix = QPixmap.fromImage(qimg).scaled(
                self._preview.width(),
                self._preview.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._preview.setPixmap(pix)
        except Exception as e:
            self._preview.setText(f"截屏失败：{e}\n（请检查环境/权限）")

    def _on_save(self) -> None:
        # 适配保存待 Sprint 0/1 实做：通过 region_picker 流程 + 多次框选
        self._preview.setText("（保存适配功能待整合 region_picker 流程）")
