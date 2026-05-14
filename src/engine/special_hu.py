"""特殊胡型集中判定（见 docs/07 §7）。

分两类：

A. **结构兼容 5 门子**（仅触发条件特殊）：
   - 天胡 TIAN_HU：庄家起手即成 5 门子完整
   - 地胡 DI_HU：闲家胡庄家首打
   - 五福 WU_FU：4 碰报警后凑成 5 个碰 (k=0, m=0, j=5)

B. **不属 5 门子**（特殊起手胡）：
   - 小七对 XIAO_QI_DUI：14 张恰好 7 对
   - 双龙 SHUANG_LONG：起手 2 个一提

判定函数返回 None 或 WinKind 枚举值。
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from src.engine.hand import Hand
from src.engine.tiles import Tile
from src.engine.win_check import (
    check_shuang_long,
    check_xiao_qi_dui,
    standard_can_win,
)


class WinKind(str, Enum):
    NORMAL = "normal"          # 普通 5 门子胡
    TIAN_HU = "tian_hu"        # 天胡
    DI_HU = "di_hu"            # 地胡
    WU_FU = "wu_fu"            # 五福
    XIAO_QI_DUI = "xiao_qi_dui"  # 小七对
    SHUANG_LONG = "shuang_long"  # 双龙


@dataclass
class WinContext:
    """状态机给胡牌判定的上下文（用于区分特殊胡型）。"""
    is_dealer: bool = False             # 是否庄家
    turn_number: int = 0                # 已进行的回合数（0=首轮未打牌）
    is_dealer_first_discard: bool = False  # 当前 win_tile 是否是庄家首打
    is_baojing: bool = False            # 当前胡牌者是否处于五福报警状态


def classify_win(
    hand: Hand,
    win_tile: Optional[Tile] = None,
    context: Optional[WinContext] = None,
) -> Optional[WinKind]:
    """综合判定胡型种类。返回 WinKind 或 None（不胡）。

    优先级：
    1. 不属 5 门子的特殊起手胡（小七对/双龙）
    2. 5 门子胡 → 按 context 进一步分天胡/地胡/五福/普通
    """
    if check_xiao_qi_dui(hand, win_tile):
        return WinKind.XIAO_QI_DUI
    if check_shuang_long(hand, win_tile):
        return WinKind.SHUANG_LONG

    if not standard_can_win(hand, win_tile):
        return None

    if context is None:
        return WinKind.NORMAL

    # 5 门子结构下进一步区分
    if context.is_dealer and context.turn_number == 0:
        # 庄家起手即成 5 门子 → 天胡
        return WinKind.TIAN_HU
    if not context.is_dealer and context.is_dealer_first_discard:
        # 闲家胡庄家首打 → 地胡
        return WinKind.DI_HU
    if context.is_baojing and _is_wu_fu_structure(hand):
        # 报警 + 5 碰全 → 五福
        return WinKind.WU_FU

    return WinKind.NORMAL


def _is_wu_fu_structure(hand: Hand) -> bool:
    """五福 = 副露全是碰（5 个 peng meld）。"""
    pengs = sum(1 for m in hand.melds if m.type == "peng")
    return pengs >= 5
