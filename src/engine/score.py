"""积分计算（按 docs/07 §6）。

胡牌时分数取决于：
- 胡的方式：自摸（每人给）/ 放炮（出牌者给）
- 胡的牌型来源：普通胡 / 碰牌胡 / 偎牌胡 / 跑牌胡 / 提牌胡

特殊胡型（天胡/地胡/五福/小七对/双龙）走独立分数表。
中庄/连中机制由状态机在多局间累计，本模块只给"单局基础分"。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from src.engine.hand import Hand


WinKind = Literal[
    "normal",      # 普通胡
    "peng_hu",     # 碰牌胡（胡的那张和已碰过的同字号 / 用碰过的牌组成胡型）
    "wei_hu",      # 偎牌胡
    "pao_hu",      # 跑牌胡
    "ti_hu",       # 提牌胡
    "tian_hu",     # 天胡（庄家胡亮张）
    "di_hu",       # 地胡（闲家胡庄家首打）
    "wu_fu",       # 五福
    "xiao_qi_dui", # 小七对
    "shuang_long", # 双龙
]

SOURCE_SELF_DRAW = "self_draw"   # 自摸
SOURCE_DIANPAO = "dianpao"       # 放炮（胡别家打的）


# 胡摸的牌：每人给（× 3 家）
SCORE_DRAW_PER_PLAYER: dict[str, int] = {
    "normal": 4,
    "peng_hu": 5,
    "wei_hu": 6,
    "pao_hu": 8,
    "ti_hu": 12,
}

# 胡打出的牌：放炮者给
SCORE_DIANPAO: dict[str, int] = {
    "normal": 12,
    "peng_hu": 15,
    "pao_hu": 24,
    # 注：截图未列出 wei_hu/ti_hu 放炮分，按线性外推；⚠️ 实战核对
    "wei_hu": 18,
    "ti_hu": 36,
}

# 特殊胡型
SCORE_TIAN_HU_PER_PLAYER = 10
SCORE_DI_HU_FROM_DEALER = 24
SCORE_WU_FU_DRAW_PER_PLAYER = 40
SCORE_WU_FU_DIANPAO = 120
SCORE_XIAO_QI_DUI_PER_PLAYER = 40
SCORE_SHUANG_LONG_PER_PLAYER = 40


@dataclass
class WinScore:
    """单局胡牌的分数明细。"""
    kind: str
    source: str
    base_score: int   # 自摸时是"每人给的分"，放炮时是"放炮者给的分"
    total_received: int  # 胡牌方实际收到的总分（自摸 = base × 3）

    @classmethod
    def for_normal_win(cls, kind: str, source: str) -> "WinScore":
        if source == SOURCE_SELF_DRAW:
            base = SCORE_DRAW_PER_PLAYER.get(kind, 0)
            return cls(kind, source, base, base * 3)
        elif source == SOURCE_DIANPAO:
            base = SCORE_DIANPAO.get(kind, 0)
            return cls(kind, source, base, base)
        raise ValueError(f"未知 source: {source}")

    @classmethod
    def for_special(cls, kind: str, source: str) -> "WinScore":
        if kind == "tian_hu":
            return cls(kind, source, SCORE_TIAN_HU_PER_PLAYER,
                       SCORE_TIAN_HU_PER_PLAYER * 3)
        if kind == "di_hu":
            return cls(kind, source, SCORE_DI_HU_FROM_DEALER,
                       SCORE_DI_HU_FROM_DEALER)
        if kind == "wu_fu":
            if source == SOURCE_SELF_DRAW:
                return cls(kind, source, SCORE_WU_FU_DRAW_PER_PLAYER,
                           SCORE_WU_FU_DRAW_PER_PLAYER * 3)
            return cls(kind, source, SCORE_WU_FU_DIANPAO, SCORE_WU_FU_DIANPAO)
        if kind == "xiao_qi_dui":
            return cls(kind, source, SCORE_XIAO_QI_DUI_PER_PLAYER,
                       SCORE_XIAO_QI_DUI_PER_PLAYER * 3)
        if kind == "shuang_long":
            return cls(kind, source, SCORE_SHUANG_LONG_PER_PLAYER,
                       SCORE_SHUANG_LONG_PER_PLAYER * 3)
        raise ValueError(f"未知特殊胡: {kind}")


def estimate_win_kind(hand: Hand) -> str:
    """根据手牌副露猜胡牌类型（粗略）：
    - 含 ti 副露 → ti_hu
    - 含 pao 副露 → pao_hu
    - 含 wei 副露 → wei_hu
    - 含 peng 副露 → peng_hu
    - 否则 normal

    实际游戏中 kind 由"胡的那张牌的来源"决定，本函数只给个保守估计，
    用于蒙特卡洛模拟时计算期望积分。
    """
    types = {m.type for m in hand.melds}
    if "ti" in types or "an_ti" in types:
        return "ti_hu"
    # pao 在副露里通常表现为 ti（坎升提）
    if "wei" in types:
        return "wei_hu"
    if "peng" in types:
        return "peng_hu"
    return "normal"
