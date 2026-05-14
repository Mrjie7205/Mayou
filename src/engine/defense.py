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
    passed_tiles: list[Tile] = field(default_factory=list)  # 该家已过张的字（不能再吃/碰）


@dataclass
class DefenseScore:
    tile: Tile
    safety: float                       # 0..1, 1=最安全
    per_seat: dict[str, float] = field(default_factory=dict)


def is_genbutsu(tile: Tile, opp: OpponentInfo) -> bool:
    return tile in opp.discards


def is_jin(tile: Tile, opp: OpponentInfo) -> bool:
    """筋：对方打过同字号 5 → 2、8 安全；打过 4 → 1、7 安全；打过 6 → 3、9 安全。

    **重要硬拦截**：tile.num ∈ {2,7,10} 不应用筋逻辑。
    原因：字牌「2-7-10」特殊连张 + 红色字号绞牌结构，让 2/7/10 的"安全推断"失效。
    例：对家打了 2，他可能仍持有 7/10 想凑「二七十」句话或绞牌，7 和 10 不安全。
    （Gemini 2026-05 评审建议）
    """
    if tile.num in (2, 7, 10):
        return False
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
    """对单个对手的安全度估算（0..1，1=最安全）。

    优先级（早返回）：
    1. 现物         → safety 1.0
    2. 过张         → safety 0.95（他失去了对该字号的吃/碰权）
    3. 五福报警家   → 跑胡候选 0.0；其他 0.85（报警限缩听张范围，生张反而安全）
    4. 绝张（≥3 见）→ safety 0.85-0.92（对家最多 1 张，无法碰/跑/提）
    5. 通用计算（碰过+筋+红色加成）

    （Gemini 2026-05 评审建议：过张追踪、报警重写、绝张判定 三项重写）
    """
    if is_genbutsu(tile, opp):
        return 1.0

    if tile in opp.passed_tiles:
        return 0.95

    if opp.is_baojing:
        meld_tiles = {t for _type, ts in opp.melds for t in ts}
        if tile in meld_tiles:
            # 跑胡候选：对家碰/偎过的字号，他再摸到/被打到能"跑"
            return 0.0
        # 报警家其他字号反而比未报警时更安全
        # 他只能胡五福（凑那对手里看不见的字号）+ 跑胡（已副露字号）
        # 我们看不到他手里那对，简化为通用低危
        return 0.85

    # 绝张：该字号已可见 ≥3 张，对家最多剩 1 张
    # 不能形成碰（需 2 张+1）、不能跑（需坎+1 或 偎+1）、不能提（需 4 张）
    # 仅小概率被吃（句话/绞牌）或单吊将
    visible_count = all_visible.get(tile, 0)
    if visible_count >= 3:
        return 0.85 if tile.is_red else 0.92

    danger = 0.0
    meld_tiles = {t for _type, ts in opp.melds for t in ts}
    if tile in meld_tiles:
        danger += 0.2
    if is_jin(tile, opp):
        danger -= 0.15  # Gemini 评审：从 -0.3 降权（字牌筋效力弱于麻将）
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
