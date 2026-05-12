"""帧间差分推断游戏事件。

输入：连续两帧的识别结果（每个区域有哪些牌）
输出：推断出的事件列表

Sprint 4 实做。当前为占位/接口定义。
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from src.engine.tiles import Tile
from src.state.events import Event, Seat


@dataclass
class FrameObservation:
    """单帧识别结果。每个区域 → 牌列表。"""
    my_hand: list[Tile]
    discards: dict[Seat, list[Tile]]
    melds: dict[Seat, list[tuple[str, tuple[Tile, ...]]]]
    baojing_seats: set[Seat]
    timestamp: float = 0.0


def detect_events(
    prev: FrameObservation | None,
    curr: FrameObservation,
) -> list[Event]:
    """对比两帧识别结果，推断发生的事件。

    简化版：只检测 discard 和 baojing 触发。
    完整规则待 Sprint 4 实做。
    """
    events: list[Event] = []
    if prev is None:
        return events

    for seat, curr_discards in curr.discards.items():
        prev_discards = prev.discards.get(seat, [])
        added = _diff(curr_discards, prev_discards)
        for tile in added:
            events.append(Event(
                type="discard", seat=seat, tile=tile, t=curr.timestamp,
            ))

    new_baojing = curr.baojing_seats - prev.baojing_seats
    for seat in new_baojing:
        events.append(Event(type="baojing", seat=seat, t=curr.timestamp))

    return events


def _diff(curr: list[Tile], prev: list[Tile]) -> list[Tile]:
    a = Counter(curr)
    b = Counter(prev)
    a.subtract(b)
    return [t for t, c in a.items() for _ in range(max(c, 0))]
