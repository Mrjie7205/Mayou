"""按区域识别多张牌。

策略：strip_image 是某区域裁剪图（如手牌区一长条），按等距分 N 格 →
每格做一次 match_one。

牌可能不严格等距（特别是云手机视频流压缩后），Sprint 2 要做更鲁棒的
"找牌边界"算法。这里先 MVP 用等分。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.engine.tiles import Tile
from src.recognize.template_loader import template_kind_to_tile
from src.recognize.template_match import MatchResult, match_one


@dataclass
class TileRecognition:
    tile: Optional[Tile]   # None = 背面 / 未识别
    confidence: float
    bbox: tuple[int, int, int, int]  # x, y, w, h


def recognize_strip(
    strip_image,
    templates: dict,
    expected_count: int,
) -> list[TileRecognition]:
    if strip_image is None or strip_image.size == 0:
        return []
    h, w = strip_image.shape[:2]
    if expected_count <= 0 or w <= 0:
        return []

    cell_w = w // expected_count
    out: list[TileRecognition] = []
    for i in range(expected_count):
        x_start = i * cell_w
        x_end = w if i == expected_count - 1 else (i + 1) * cell_w
        cell = strip_image[:, x_start:x_end]
        match = match_one(cell, templates)
        if match is None:
            out.append(TileRecognition(
                tile=None, confidence=0.0,
                bbox=(x_start, 0, x_end - x_start, h),
            ))
        else:
            out.append(TileRecognition(
                tile=template_kind_to_tile(match.kind),
                confidence=match.confidence,
                bbox=(x_start, 0, x_end - x_start, h),
            ))
    return out


def crop(image, bbox: tuple[int, int, int, int]):
    x, y, w, h = bbox
    return image[y:y + h, x:x + w]
