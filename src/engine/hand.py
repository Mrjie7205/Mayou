"""手牌容器 + 副露（已落桌的组）。"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable, Literal

from src.engine.tiles import Tile


MeldType = Literal["peng", "wei", "ti", "chi_jvhua", "chi_jiao", "an_ke", "an_ti"]


@dataclass(frozen=True)
class Meld:
    """副露区一组。

    type:
      - peng       碰（3 张相同，全明）
      - wei        偎（3 张相同，1 明 2 暗）
      - ti         提（4 张相同，1 明 3 暗，由 wei/an_ke 升级或一开始就是 4 张）
      - chi_jvhua  吃成的一句话（3 张连续）
      - chi_jiao   吃成的绞牌（大对+小单 或 反之）
      - an_ke      暗刻（坎，3 张相同手里持有，未公开）
      - an_ti      暗提（4 张相同手里持有，未公开）
    """
    type: str
    tiles: tuple[Tile, ...]

    @property
    def size(self) -> int:
        return len(self.tiles)

    @property
    def represents_triplet(self) -> bool:
        # 占胡牌型里"1 个组件"位置（无论 3 张 4 张都算 1 组件）
        return self.type in ("peng", "wei", "ti", "an_ke", "an_ti")

    @property
    def represents_jvhua(self) -> bool:
        return self.type == "chi_jvhua"

    @property
    def represents_jiao(self) -> bool:
        return self.type == "chi_jiao"


@dataclass
class Hand:
    """完整手牌 = 暗手（手里看不见的）+ 副露（已落桌）。"""
    closed: Counter = field(default_factory=Counter)
    melds: list[Meld] = field(default_factory=list)

    @classmethod
    def from_tiles(cls, tiles: Iterable[Tile], melds: Iterable[Meld] = ()) -> "Hand":
        return cls(closed=Counter(tiles), melds=list(melds))

    def closed_size(self) -> int:
        return sum(self.closed.values())

    def total_size(self) -> int:
        return self.closed_size() + sum(m.size for m in self.melds)

    def add(self, tile: Tile) -> None:
        self.closed[tile] += 1

    def remove(self, tile: Tile) -> None:
        if self.closed[tile] <= 0:
            raise ValueError(f"手里没有 {tile}")
        self.closed[tile] -= 1
        if self.closed[tile] == 0:
            del self.closed[tile]

    def copy(self) -> "Hand":
        return Hand(closed=Counter(self.closed), melds=list(self.melds))

    def all_visible_tiles(self) -> list[Tile]:
        out = list(self.closed.elements())
        for m in self.melds:
            out.extend(m.tiles)
        return out
