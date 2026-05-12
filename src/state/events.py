"""牌局事件定义。

事件由识别层和 UI 修正按钮触发。状态机消费事件 → 更新 GameState + 写复盘日志。

事件类型：
- deal:    发牌起手
- draw:    摸牌
- discard: 打牌
- peng:    碰
- wei:     偎（强制，摸到自对子）
- ti:      提（强制，摸到自坎或偎过的牌）
- pao:     跑（坎升提 / 偎牌被摸/打 / 碰过的被摸）
- chi:     吃（成一句话或绞牌）
- ren:     忍碰（放弃碰）
- guo_zhang: 过张（错过吃/碰失权）
- baojing: 五福报警（4 碰后强制声明）
- hu:      胡牌
- chou_zhuang: 臭庄（流局）
- engine_recommend: 引擎建议（用于复盘对照）
- manual_correction: 人工修正
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Optional

from src.engine.tiles import Tile


Seat = Literal["self", "left", "across", "right"]
DEFAULT_SEATS: tuple[Seat, ...] = ("self", "left", "across", "right")


@dataclass
class Event:
    type: str
    seat: Optional[Seat] = None
    tile: Optional[Tile] = None
    tiles: tuple[Tile, ...] = ()
    t: float = 0.0          # 相对秒（局开始为 0）
    confidence: float = 1.0  # 识别置信度 [0..1]
    note: str = ""           # 备注（manual 修正时填理由等）
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        d: dict = {"type": self.type, "t": round(self.t, 3)}
        if self.seat is not None:
            d["seat"] = self.seat
        if self.tile is not None:
            d["tile"] = self.tile.code
        if self.tiles:
            d["tiles"] = [t.code for t in self.tiles]
        if self.confidence < 1.0:
            d["confidence"] = round(self.confidence, 3)
        if self.note:
            d["note"] = self.note
        if self.extra:
            d["extra"] = self.extra
        return d
