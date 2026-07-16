"""Room — a single hotel room with type, price, and status."""

from __future__ import annotations

from hms.models.enums import RoomStatus, RoomStyle
from hms.models.housekeeping import HouseKeeping
from hms.models.room_key import RoomKey


class Room:
    def __init__(
        self,
        number: str,
        style: RoomStyle,
        price: float,
        capacity: int = 2,
        amenities: list[str] | None = None,
    ) -> None:
        if price < 0:
            raise ValueError("Room price cannot be negative.")
        self._number = number
        self._style = style
        self._status = RoomStatus.AVAILABLE
        self._price = price
        self._capacity = capacity
        self._amenities = amenities or []
        self._room_key: RoomKey | None = None
        self._housekeeping = HouseKeeping(number)

    @property
    def number(self) -> str:
        return self._number

    @property
    def style(self) -> RoomStyle:
        return self._style

    @property
    def status(self) -> RoomStatus:
        return self._status

    @property
    def price(self) -> float:
        return self._price

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def amenities(self) -> list[str]:
        return list(self._amenities)

    @property
    def room_key(self) -> RoomKey | None:
        return self._room_key

    @property
    def housekeeping(self) -> HouseKeeping:
        return self._housekeeping

    def set_price(self, price: float) -> None:
        if price < 0:
            raise ValueError("Room price cannot be negative.")
        self._price = price

    def set_status(self, status: RoomStatus) -> None:
        self._status = status

    def issue_key(self) -> RoomKey:
        key = RoomKey(assigned_room_number=self._number)
        self._room_key = key
        return key

    def attach_key(self, key: RoomKey) -> None:
        self._room_key = key

    def revoke_key(self) -> None:
        if self._room_key:
            self._room_key.revoke()
            self._room_key = None

    def matches_filter(
        self,
        style: RoomStyle | None = None,
        max_price: float | None = None,
    ) -> bool:
        if style is not None and self._style != style:
            return False
        if max_price is not None and self._price > max_price:
            return False
        return True

    def __str__(self) -> str:
        return (
            f"Room {self._number} | {self._style.value} | "
            f"R{self._price:.2f}/night | {self._status.value}"
        )
