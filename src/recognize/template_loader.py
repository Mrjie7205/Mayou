"""模板库加载。

目录结构（来自 docs/02）：
    assets/templates/<platform>/tiles/<kind>/*.png
    kind 命名约定：lower_1..lower_10, upper_1..upper_10, back
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from src.engine.tiles import Tile


TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "assets" / "templates"


def template_kind_to_tile(kind: str) -> Optional[Tile]:
    if kind == "back":
        return None
    if kind.startswith("lower_"):
        return Tile("L", int(kind[6:]))
    if kind.startswith("upper_"):
        return Tile("U", int(kind[6:]))
    raise ValueError(f"未知模板 kind: {kind!r}")


def tile_to_template_kind(tile: Optional[Tile]) -> str:
    if tile is None:
        return "back"
    prefix = "lower_" if tile.case == "L" else "upper_"
    return f"{prefix}{tile.num}"


def template_dir_for(platform: str, kind: str) -> Path:
    return TEMPLATES_DIR / platform / "tiles" / kind


def load_templates(platform: str):
    """加载 platform 的所有模板。返回 {kind: [ndarray, ...]}。

    依赖 cv2，按需 import 避免无 OpenCV 环境时 import 模块就崩。
    """
    import cv2

    base = TEMPLATES_DIR / platform / "tiles"
    if not base.exists():
        return {}
    out: dict = {}
    for kind_dir in sorted(base.iterdir()):
        if not kind_dir.is_dir():
            continue
        imgs = []
        for f in sorted(kind_dir.glob("*.png")):
            img = cv2.imread(str(f))
            if img is not None:
                imgs.append(img)
        if imgs:
            out[kind_dir.name] = imgs
    return out


def template_summary(platform: str) -> dict[str, int]:
    """返回 {kind: 张数}，用于 UI 显示模板覆盖度。"""
    base = TEMPLATES_DIR / platform / "tiles"
    summary: dict[str, int] = {}
    if not base.exists():
        return summary
    for kind_dir in base.iterdir():
        if kind_dir.is_dir():
            summary[kind_dir.name] = len(list(kind_dir.glob("*.png")))
    return summary
