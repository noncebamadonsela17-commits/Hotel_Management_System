"""RoomKey — access credential for a room."""

from __future__ import annotations

import uuid


class RoomKey:
    def __init__(self, assigned_room_number: str | None = None) -> None:
        self._key_id = str(uuid.uuid4())[:8].upper()
        self._barcode = f"RK-{self._key_id}"
        self._assigned_room: str | None = assigned_room_number

    @property
    def key_id(self) -> str:
        return self._key_id

    @property
    def barcode(self) -> str:
        return self._barcode

    @property
    def assigned_room(self) -> str | None:
        return self._assigned_room

    def assign_to(self, room_number: str) -> None:
        self._assigned_room = room_number

    def revoke(self) -> None:
        self._assigned_room = None

    @classmethod
    def restore(cls, key_id: str, barcode: str, assigned_room: str) -> RoomKey:
        key = cls(assigned_room_number=assigned_room)
        key._key_id = key_id
        key._barcode = barcode
        return key

    def __str__(self) -> str:
        room = self._assigned_room or "unassigned"
        return f"RoomKey({self._barcode}, room={room})"
