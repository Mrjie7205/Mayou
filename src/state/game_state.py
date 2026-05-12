"""GameState：完整局面快照。

包含 4 家信息 + 牌墩剩余 + 五福报警状态 + 当前轮次。
事件应用是单向的：apply_event(event) → 更新内部状态。
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from src.engine.hand import Hand, Meld
from src.engine.tiles import ALL_KINDS, DECK_COUNT_PER_KIND, Tile
from src.state.events import DEFAULT_SEATS, Event, Seat


@dataclass
class SeatState:
    seat: Seat
    hand: Hand = field(default_factory=Hand)  # 自己有暗手；他家暗手不可见为空
    discards: list[Tile] = field(default_factory=list)
    peng_count: int = 0
    is_baojing: bool = False
    is_winner: bool = False


@dataclass
class GameState:
    seats: dict[Seat, SeatState] = field(
        default_factory=lambda: {s: SeatState(s) for s in DEFAULT_SEATS}
    )
    dealer: Seat = "self"
    current_turn: Seat = "self"
    deck_remaining: int = 23  # docs/07 §2：庄 15 + 闲 14×3 + 墩 23 = 80
    last_drawn_tile: Tile | None = None
    finished: bool = False
    history: list[Event] = field(default_factory=list)

    @classmethod
    def fresh(cls, dealer: Seat = "self") -> "GameState":
        gs = cls()
        gs.dealer = dealer
        gs.current_turn = dealer
        return gs

    def apply_event(self, event: Event) -> None:
        self.history.append(event)
        handler = _HANDLERS.get(event.type)
        if handler is not None:
            handler(self, event)

    def remaining_kind_count(self, tile: Tile) -> int:
        seen = 0
        for s in self.seats.values():
            seen += sum(1 for d in s.discards if d == tile)
            for m in s.hand.melds:
                seen += sum(1 for t in m.tiles if t == tile)
        seen += self.seats["self"].hand.closed.get(tile, 0)
        return DECK_COUNT_PER_KIND - seen

    def remaining_counter(self) -> Counter:
        return Counter({k: self.remaining_kind_count(k) for k in ALL_KINDS})

    def all_visible_tiles(self) -> Counter:
        c: Counter = Counter()
        for s in self.seats.values():
            c.update(s.discards)
            for m in s.hand.melds:
                c.update(m.tiles)
        return c


def _on_deal(gs: GameState, ev: Event) -> None:
    if ev.seat == "self" and ev.tiles:
        gs.seats["self"].hand = Hand.from_tiles(ev.tiles)
    if "dealer" in ev.extra:
        gs.dealer = ev.extra["dealer"]
        gs.current_turn = ev.extra["dealer"]


def _on_draw(gs: GameState, ev: Event) -> None:
    gs.deck_remaining = max(0, gs.deck_remaining - 1)
    if ev.seat == "self" and ev.tile is not None:
        gs.seats["self"].hand.add(ev.tile)
        gs.last_drawn_tile = ev.tile


def _on_discard(gs: GameState, ev: Event) -> None:
    if ev.tile is None or ev.seat is None:
        return
    if ev.seat == "self":
        try:
            gs.seats["self"].hand.remove(ev.tile)
        except ValueError:
            pass
    gs.seats[ev.seat].discards.append(ev.tile)
    gs.last_drawn_tile = None


def _on_peng(gs: GameState, ev: Event) -> None:
    if ev.tile is None or ev.seat is None:
        return
    seat = gs.seats[ev.seat]
    if ev.seat == "self":
        for _ in range(2):
            try:
                seat.hand.remove(ev.tile)
            except ValueError:
                break
    seat.hand.melds.append(Meld("peng", (ev.tile,) * 3))
    seat.peng_count += 1


def _on_wei(gs: GameState, ev: Event) -> None:
    if ev.tile is None or ev.seat is None:
        return
    seat = gs.seats[ev.seat]
    if ev.seat == "self":
        for _ in range(2):
            try:
                seat.hand.remove(ev.tile)
            except ValueError:
                break
    seat.hand.melds.append(Meld("wei", (ev.tile,) * 3))


def _on_ti(gs: GameState, ev: Event) -> None:
    if ev.tile is None or ev.seat is None:
        return
    seat = gs.seats[ev.seat]
    if ev.seat == "self":
        # 提牌：升级已有的 wei 或新增 4 张组
        for i, m in enumerate(seat.hand.melds):
            if m.type == "wei" and m.tiles[0] == ev.tile:
                seat.hand.melds[i] = Meld("ti", (ev.tile,) * 4)
                try:
                    seat.hand.remove(ev.tile)
                except ValueError:
                    pass
                return
        # 否则手里有坎/偎过：新建 ti
        for _ in range(3):
            try:
                seat.hand.remove(ev.tile)
            except ValueError:
                break
    seat.hand.melds.append(Meld("ti", (ev.tile,) * 4))


def _on_pao(gs: GameState, ev: Event) -> None:
    # 跑：坎升提 / 偎被摸/打 / 碰过被摸
    # 简化：升级已有的 peng/wei 为 ti
    if ev.tile is None or ev.seat is None:
        return
    seat = gs.seats[ev.seat]
    for i, m in enumerate(seat.hand.melds):
        if m.type in ("peng", "wei") and m.tiles[0] == ev.tile:
            seat.hand.melds[i] = Meld("ti", (ev.tile,) * 4)
            return
    seat.hand.melds.append(Meld("ti", (ev.tile,) * 4))


def _on_chi(gs: GameState, ev: Event) -> None:
    if ev.seat is None or not ev.tiles:
        return
    seat = gs.seats[ev.seat]
    chi_type = ev.extra.get("chi_type", "chi_jvhua")
    if ev.seat == "self":
        for t in ev.tiles[:-1]:
            try:
                seat.hand.remove(t)
            except ValueError:
                pass
    seat.hand.melds.append(Meld(chi_type, tuple(ev.tiles)))


def _on_baojing(gs: GameState, ev: Event) -> None:
    if ev.seat is not None:
        gs.seats[ev.seat].is_baojing = True


def _on_hu(gs: GameState, ev: Event) -> None:
    gs.finished = True
    if ev.seat is not None:
        gs.seats[ev.seat].is_winner = True


def _on_chou_zhuang(gs: GameState, _ev: Event) -> None:
    gs.finished = True


_HANDLERS = {
    "deal": _on_deal,
    "draw": _on_draw,
    "discard": _on_discard,
    "peng": _on_peng,
    "wei": _on_wei,
    "ti": _on_ti,
    "pao": _on_pao,
    "chi": _on_chi,
    "baojing": _on_baojing,
    "hu": _on_hu,
    "chou_zhuang": _on_chou_zhuang,
}
