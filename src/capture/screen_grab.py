"""屏幕截图：用 mss 抓指定矩形或整屏。

返回的 ndarray 为 BGR uint8（OpenCV 兼容格式）。
"""
from dataclasses import dataclass

import mss
import numpy as np


@dataclass(frozen=True)
class Region:
    x: int
    y: int
    w: int
    h: int

    def as_mss_monitor(self) -> dict:
        return {"left": self.x, "top": self.y, "width": self.w, "height": self.h}


def grab_region(region: Region) -> np.ndarray:
    with mss.mss() as sct:
        raw = sct.grab(region.as_mss_monitor())
        return np.ascontiguousarray(np.array(raw)[:, :, :3])


def grab_primary_screen() -> np.ndarray:
    with mss.mss() as sct:
        raw = sct.grab(sct.monitors[1])
        return np.ascontiguousarray(np.array(raw)[:, :, :3])
