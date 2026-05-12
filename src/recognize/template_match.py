"""单图块多尺度模板匹配。

对一张候选图块，跟所有模板比对，返回最匹配的 kind + 置信度。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


DEFAULT_SCALES = (0.85, 0.92, 1.0, 1.08, 1.15)
DEFAULT_THRESHOLD = 0.6


@dataclass
class MatchResult:
    kind: str
    confidence: float


def match_one(
    target,
    templates: dict,
    *,
    scales: tuple[float, ...] = DEFAULT_SCALES,
    threshold: float = DEFAULT_THRESHOLD,
) -> Optional[MatchResult]:
    """target: 目标图块（ndarray BGR），templates: {kind: [ndarray, ...]}。

    返回最匹配的 MatchResult 或 None（低于阈值）。
    """
    import cv2

    if target is None or target.size == 0:
        return None
    target_h, target_w = target.shape[:2]

    best_kind: Optional[str] = None
    best_score = 0.0

    for kind, imgs in templates.items():
        for tmpl in imgs:
            for scale in scales:
                new_w = int(tmpl.shape[1] * scale)
                new_h = int(tmpl.shape[0] * scale)
                if new_w < 5 or new_h < 5:
                    continue
                if new_w > target_w or new_h > target_h:
                    continue
                resized = cv2.resize(tmpl, (new_w, new_h))
                res = cv2.matchTemplate(target, resized, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(res)
                if max_val > best_score:
                    best_score = float(max_val)
                    best_kind = kind

    if best_kind is None or best_score < threshold:
        return None
    return MatchResult(kind=best_kind, confidence=best_score)
