"""HouseKeeping — cleaning / maintenance history for a room."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class LogEntry:
    timestamp: datetime
    staff_name: str
    activity: str
    notes: str = ""

    def __str__(self) -> str:
        note = f" — {self.notes}" if self.notes else ""
        return (
            f"[{self.timestamp.strftime('%Y-%m-%d %H:%M')}] "
            f"{self.staff_name}: {self.activity}{note}"
        )


class HouseKeeping:
    def __init__(self, room_number: str) -> None:
        self._room_id = room_number
        self._log_entries: list[LogEntry] = []
        self._last_cleaned: datetime | None = None

    @property
    def room_id(self) -> str:
        return self._room_id

    @property
    def log_entries(self) -> list[LogEntry]:
        return list(self._log_entries)

    @property
    def last_cleaned(self) -> datetime | None:
        return self._last_cleaned

    def add_log(
        self, staff_name: str, activity: str, notes: str = "", mark_cleaned: bool = False
    ) -> LogEntry:
        entry = LogEntry(
            timestamp=datetime.now(),
            staff_name=staff_name,
            activity=activity,
            notes=notes,
        )
        self._log_entries.append(entry)
        if mark_cleaned or "clean" in activity.lower():
            self._last_cleaned = entry.timestamp
        return entry

    def restore_entry(self, entry: LogEntry, last_cleaned: datetime | None = None) -> None:
        self._log_entries.append(entry)
        if last_cleaned is not None:
            self._last_cleaned = last_cleaned
        elif "clean" in entry.activity.lower():
            self._last_cleaned = entry.timestamp

    def set_last_cleaned(self, when: datetime | None) -> None:
        self._last_cleaned = when

    def __str__(self) -> str:
        last = (
            self._last_cleaned.strftime("%Y-%m-%d %H:%M")
            if self._last_cleaned
            else "never"
        )
        return f"HouseKeeping(room={self._room_id}, entries={len(self._log_entries)}, last_cleaned={last})"
