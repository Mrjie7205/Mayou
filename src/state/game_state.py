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
    passed_tiles: list[Tile] = field(default_factory=list)  # 该家已过张的字（不能再吃/碰）


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
    # 为特殊胡型判定提供上下文（天胡/地胡/五福，见 special_hu.py）
    turn_number: int = 0           # 已进行的回合数（discard 事件计数）
    dealer_first_tile: Tile | None = None  # 庄家首打的牌（用于地胡）

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
    # 记录庄家首打（用于地胡判定）
    if (
        gs.dealer_first_tile is None
        and ev.seat == gs.dealer
        and gs.turn_number == 0
    ):
        gs.dealer_first_tile = ev.tile
    gs.turn_number += 1


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
    """偎：摸到自己手里的对子，强制公开 3 张（1 明 2 暗）。

    self 时：draw 事件已把摸到的牌加进 closed，偎动作把这 3 张（原对子 + 新摸）
    全部转 meld → 应从 closed 扣 3 张（不是 2 张）。
    """
    if ev.tile is None or ev.seat is None:
        return
    seat = gs.seats[ev.seat]
    if ev.seat == "self":
        for _ in range(3):
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
        # 优先升级已有的 wei / an_ke 为 ti，避免出现幽灵 meld
        for i, m in enumerate(seat.hand.melds):
            if m.type in ("wei", "an_ke") and m.tiles and m.tiles[0] == ev.tile:
                seat.hand.melds[i] = Meld("ti", (ev.tile,) * 4)
                try:
                    seat.hand.remove(ev.tile)
                except ValueError:
                    pass
                return
        # 起手就持 4 张：从 closed 整组扣除后新增 ti
        for _ in range(4):
            try:
                seat.hand.remove(ev.tile)
            except ValueError:
                break
    seat.hand.melds.append(Meld("ti", (ev.tile,) * 4))


def _on_pao(gs: GameState, ev: Event) -> None:
    """跑：peng/wei 升级为 ti。

    self 触发场景：
    (a) 自摸到已碰/偎过的字号 → draw 事件先 add 1 张到 closed → 跑动作扣 1 张
    (b) 别人打/摸的牌是自己已碰的 → closed 不动（外部 1 张进 meld）

    简化：self 且 closed 里有这张 → 扣 1 张；否则视为外部触发不动。
    """
    if ev.tile is None or ev.seat is None:
        return
    seat = gs.seats[ev.seat]
    if ev.seat == "self" and seat.hand.closed.get(ev.tile, 0) >= 1:
        try:
            seat.hand.remove(ev.tile)
        except ValueError:
            pass
    for i, m in enumerate(seat.hand.melds):
        if m.type in ("peng", "wei") and m.tiles and m.tiles[0] == ev.tile:
            seat.hand.melds[i] = Meld("ti", (ev.tile,) * 4)
            return
    seat.hand.melds.append(Meld("ti", (ev.tile,) * 4))


def _on_chi(gs: GameState, ev: Event) -> None:
    if ev.seat is None or len(ev.tiles) < 3:
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


def _on_guo_zhang(gs: GameState, ev: Event) -> None:
    """过张：某家有机会吃/碰未行使，对该字号失去后续吃碰权。"""
    if ev.seat is None or ev.tile is None:
        return
    seat = gs.seats[ev.seat]
    if ev.tile not in seat.passed_tiles:
        seat.passed_tiles.append(ev.tile)


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
    "guo_zhang": _on_guo_zhang,
    "hu": _on_hu,
    "chou_zhuang": _on_chou_zhuang,
}
