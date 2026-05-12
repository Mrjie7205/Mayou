"""字牌牌张定义。

20 种字 × 4 张 = 80 张：
- 小写「一二三四五六七八九十」（case='L'）
- 大写「壹贰叁肆伍陆柒捌玖拾」（case='U'）
- 红色字号：每组的 2、7、10
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal


Case = Literal["L", "U"]

LOWER_NAMES = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
UPPER_NAMES = ["壹", "贰", "叁", "肆", "伍", "陆", "柒", "捌", "玖", "拾"]
RED_NUMBERS = frozenset({2, 7, 10})


@dataclass(frozen=True, order=True)
class Tile:
    case: str  # "L" or "U"
    num: int  # 1..10

    def __post_init__(self) -> None:
        if self.case not in ("L", "U"):
            raise ValueError(f"case must be 'L' or 'U', got {self.case!r}")
        if not 1 <= self.num <= 10:
            raise ValueError(f"num must be 1..10, got {self.num}")

    @property
    def is_red(self) -> bool:
        return self.num in RED_NUMBERS

    @property
    def display_name(self) -> str:
        names = LOWER_NAMES if self.case == "L" else UPPER_NAMES
        prefix = "小" if self.case == "L" else "大"
        return prefix + names[self.num - 1]

    @property
    def code(self) -> str:
        return f"{self.case}{self.num}"

    def __str__(self) -> str:
        return self.display_name


ALL_KINDS: list[Tile] = [Tile(c, n) for c in ("L", "U") for n in range(1, 11)]
DECK_COUNT_PER_KIND = 4
TOTAL_TILES = len(ALL_KINDS) * DECK_COUNT_PER_KIND  # 80


def full_deck() -> list[Tile]:
    return [t for t in ALL_KINDS for _ in range(DECK_COUNT_PER_KIND)]


def parse(s: str) -> Tile:
    s = s.strip()
    if len(s) >= 2 and s[0] in ("L", "U") and s[1:].isdigit():
        return Tile(s[0], int(s[1:]))
    if len(s) == 2 and s[0] in ("小", "大"):
        case = "L" if s[0] == "小" else "U"
        names = LOWER_NAMES if case == "L" else UPPER_NAMES
        if s[1] not in names:
            raise ValueError(f"未知字号: {s[1]!r}")
        return Tile(case, names.index(s[1]) + 1)
    raise ValueError(f"无法解析牌符: {s!r}")


def parse_many(seq: Iterable[str]) -> list[Tile]:
    return [parse(s) for s in seq]
