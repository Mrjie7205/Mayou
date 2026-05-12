"""复盘日志：每局生成一个 JSON 文件到 data/replays/。

按 docs/05 §复盘记录的字段。不存录像，只存事件流。
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from src.state.events import Event, Seat


REPLAYS_DIR = Path(__file__).resolve().parents[2] / "data" / "replays"


@dataclass
class ReplaySession:
    platform: str = "redfinger"
    started_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    ended_at: str = ""
    dealer: Seat = "self"
    rule_variant: dict[str, Any] = field(default_factory=dict)
    events: list[Event] = field(default_factory=list)
    outcome: dict[str, Any] = field(default_factory=dict)

    def append(self, event: Event) -> None:
        self.events.append(event)

    def finalize(self, outcome: dict[str, Any]) -> None:
        self.ended_at = datetime.now().isoformat(timespec="seconds")
        self.outcome = outcome

    def to_dict(self) -> dict:
        return {
            "session": {
                "platform": self.platform,
                "started_at": self.started_at,
                "ended_at": self.ended_at,
                "dealer": self.dealer,
                "rule_variant": self.rule_variant,
            },
            "events": [e.to_dict() for e in self.events],
            "outcome": self.outcome,
        }

    def save(self, dir_path: Path | None = None) -> Path:
        target_dir = dir_path or REPLAYS_DIR
        target_dir.mkdir(parents=True, exist_ok=True)
        ts = self.started_at.replace(":", "").replace("-", "")
        path = target_dir / f"{ts}-{self.dealer}.json"
        path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return path
