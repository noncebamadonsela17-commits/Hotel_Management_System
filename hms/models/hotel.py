"""Hotel — root aggregate owning rooms for a single property."""

from __future__ import annotations

from hms.models.enums import RoomStatus, RoomStyle
from hms.models.room import Room


class Hotel:
    def __init__(self, name: str, address: str) -> None:
        self._name = name
        self._address = address
        self._rooms: dict[str, Room] = {}

    @property
    def name(self) -> str:
        return self._name

    @property
    def address(self) -> str:
        return self._address

    @property
    def rooms(self) -> list[Room]:
        return list(self._rooms.values())

    def add_room(self, room: Room) -> None:
        if room.number in self._rooms:
            raise ValueError(f"Room {room.number} already exists.")
        self._rooms[room.number] = room

    def get_room(self, number: str) -> Room:
        if number not in self._rooms:
            raise KeyError(f"Room {number} not found.")
        return self._rooms[number]

    def update_room(
        self,
        number: str,
        price: float | None = None,
        status: RoomStatus | None = None,
    ) -> Room:
        room = self.get_room(number)
        if price is not None:
            room.set_price(price)
        if status is not None:
            room.set_status(status)
        return room

    def rooms_by_style(self, style: RoomStyle) -> list[Room]:
        return [r for r in self._rooms.values() if r.style == style]

    def occupancy_report(self) -> dict[str, int]:
        counts: dict[str, int] = {s.value: 0 for s in RoomStatus}
        for room in self._rooms.values():
            counts[room.status.value] += 1
        return counts

    def __str__(self) -> str:
        return f"{self._name} — {self._address} ({len(self._rooms)} rooms)"
