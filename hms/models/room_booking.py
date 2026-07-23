"""RoomBooking — reservation linking a guest to a room over a date range."""

from __future__ import annotations

import uuid
from datetime import date, timedelta

from hms.models.enums import BookingStatus
from hms.models.room_charge import RoomCharge


class RoomBooking:
    def __init__(
        self,
        room_number: str,
        guest_email: str,
        guest_name: str,
        check_in: date,
        check_out: date,
        nightly_rate: float,
    ) -> None:
        if check_out <= check_in:
            raise ValueError("Check-out date must be after check-in date.")
        self._booking_id = str(uuid.uuid4())[:8].upper()
        self._room_number = room_number
        self._guest_email = guest_email
        self._guest_name = guest_name
        self._check_in = check_in
        self._check_out = check_out
        self._nightly_rate = nightly_rate
        self._booking_status = BookingStatus.CONFIRMED
        self._charges: list[RoomCharge] = []

    @property
    def booking_id(self) -> str:
        return self._booking_id

    @property
    def room_number(self) -> str:
        return self._room_number

    @property
    def guest_email(self) -> str:
        return self._guest_email

    @property
    def guest_name(self) -> str:
        return self._guest_name

    @property
    def check_in(self) -> date:
        return self._check_in

    @property
    def check_out(self) -> date:
        return self._check_out

    @property
    def booking_status(self) -> BookingStatus:
        return self._booking_status

    @property
    def nightly_rate(self) -> float:
        return self._nightly_rate

    @property
    def charges(self) -> list[RoomCharge]:
        return list(self._charges)

    @property
    def nights(self) -> int:
        return (self._check_out - self._check_in).days

    @property
    def room_cost(self) -> float:
        return round(self.nights * self._nightly_rate, 2)

    @classmethod
    def restore(
        cls,
        booking_id: str,
        room_number: str,
        guest_email: str,
        guest_name: str,
        check_in: date,
        check_out: date,
        nightly_rate: float,
        status: BookingStatus,
        charges: list[RoomCharge] | None = None,
    ) -> RoomBooking:
        """Rebuild a booking from persisted data (keeps original IDs)."""
        booking = cls(
            room_number, guest_email, guest_name, check_in, check_out, nightly_rate
        )
        booking._booking_id = booking_id
        booking._booking_status = status
        if charges:
            booking._charges = list(charges)
        return booking

    def attach_charge(self, charge: RoomCharge) -> None:
        """Attach an already-created charge (used when loading from storage)."""
        self._charges.append(charge)

    def overlaps(self, start: date, end: date) -> bool:
        """True if [start, end) overlaps this booking's dates (exclusive checkout)."""
        if self._booking_status == BookingStatus.CANCELLED:
            return False
        return self._check_in < end and start < self._check_out

    def cancel(self) -> None:
        if self._booking_status == BookingStatus.CHECKED_IN:
            raise ValueError("Cannot cancel a booking that is already checked in.")
        if self._booking_status == BookingStatus.CHECKED_OUT:
            raise ValueError("Cannot cancel a completed booking.")
        if self._booking_status == BookingStatus.CANCELLED:
            raise ValueError("Booking is already cancelled.")
        self._booking_status = BookingStatus.CANCELLED

    def check_in_guest(self) -> None:
        if self._booking_status != BookingStatus.CONFIRMED:
            raise ValueError(
                f"Cannot check in booking with status {self._booking_status.value}."
            )
        self._booking_status = BookingStatus.CHECKED_IN

    def check_out_guest(self) -> None:
        if self._booking_status != BookingStatus.CHECKED_IN:
            raise ValueError("Guest must be checked in before check-out.")
        self._booking_status = BookingStatus.CHECKED_OUT

    def add_charge(self, description: str, amount: float) -> RoomCharge:
        if self._booking_status != BookingStatus.CHECKED_IN:
            raise ValueError("Room service can only be requested while checked in.")
        charge = RoomCharge(description, amount)
        self._charges.append(charge)
        return charge

    def dates_range(self) -> list[date]:
        return [
            self._check_in + timedelta(days=i) for i in range(self.nights)
        ]

    def __str__(self) -> str:
        return (
            f"Booking {self._booking_id} | Room {self._room_number} | "
            f"{self._guest_name} | {self._check_in} → {self._check_out} | "
            f"{self._booking_status.value}"
        )
