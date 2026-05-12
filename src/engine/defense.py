"""防守评分。

字牌「一句话」≈ 麻将顺子，所以筋/壁概念适用（见 docs/04 §4.3）。

对每张可打牌评估：被任意一家点炮的概率，给 0..1 分（1=最安全）。
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Literal

from src.engine.tiles import ALL_KINDS, DECK_COUNT_PER_KIND, Tile


SeatPosition = Literal["left", "across", "right"]


@dataclass
class OpponentInfo:
    """单个对手的可见信息。"""
    discards: list[Tile] = field(default_factory=list)
    melds: list[tuple[str, tuple[Tile, ...]]] = field(default_factory=list)
    peng_count: int = 0       # 已碰次数（用于五福报警判定）
    is_baojing: bool = False  # 五福报警状态


@dataclass
class DefenseScore:
    tile: Tile
    safety: float                       # 0..1, 1=最安全
    per_seat: dict[str, float] = field(default_factory=dict)


def is_genbutsu(tile: Tile, opp: OpponentInfo) -> bool:
    return tile in opp.discards


def is_jin(tile: Tile, opp: OpponentInfo) -> bool:
    """筋：对方打过同字号 5 → 2、8 安全；打过 4 → 1、7 安全；打过 6 → 3、9 安全。

    注：「2-7-10」特殊连张的额外筋逻辑（如打过 2 后 7、10 是否是筋）
    暂不实现，⚠️ Sprint 7 实做时细化。本函数只判定标准三连筋。
    """
    for d in opp.discards:
        if d.case != tile.case:
            continue
        if d.num == 4 and tile.num in (1, 7):
            return True
        if d.num == 5 and tile.num in (2, 8):
            return True
        if d.num == 6 and tile.num in (3, 9):
            return True
    return False


def is_bi(tile: Tile, all_visible: Counter) -> bool:
    """壁：tile 字号 4 张全可见 → 邻接搭子失效。

    Returns True 如果 tile 自己 4 张全可见（说明 tile 自己不可能再被对手用来搭句话）。
    """
    return all_visible.get(tile, 0) >= DECK_COUNT_PER_KIND


def evaluate_defense_for_seat(
    tile: Tile,
    opp: OpponentInfo,
    all_visible: Counter,
) -> float:
    """对单个对手的安全度估算（0..1，1=最安全）。"""
    if is_genbutsu(tile, opp):
        return 1.0

    danger = 0.0
    # 五福报警：威胁范围被规则限缩，但所有未弃牌都可能是听张
    if opp.is_baojing:
        danger += 0.6

    # 是不是被对方碰/偎/提过的字号附近？
    relevant_meld_tiles = [t for _type, ts in opp.melds for t in ts]
    if tile in relevant_meld_tiles:
        danger += 0.2

    if is_jin(tile, opp):
        danger -= 0.3

    if is_bi(tile, all_visible):
        danger -= 0.2

    # 红色字号天然更危险（更值钱）
    if tile.is_red:
        danger += 0.1

    safety = 1.0 - danger
    return max(0.0, min(1.0, safety))


def evaluate_defense(
    tile: Tile,
    opponents: dict[str, OpponentInfo],
    all_visible: Counter,
) -> DefenseScore:
    per_seat = {
        seat: evaluate_defense_for_seat(tile, opp, all_visible)
        for seat, opp in opponents.items()
    }
    return DefenseScore(
        tile=tile,
        safety=min(per_seat.values()) if per_seat else 1.0,
        per_seat=per_seat,
    )


def evaluate_all(
    candidate_tiles: list[Tile],
    opponents: dict[str, OpponentInfo],
    all_visible: Counter,
) -> list[DefenseScore]:
    return [
        evaluate_defense(t, opponents, all_visible)
        for t in candidate_tiles
    ]
