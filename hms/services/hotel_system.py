"""HotelSystem — orchestrates bookings, check-in/out, billing, staff, notifications."""

from __future__ import annotations

from datetime import date
from typing import Protocol

from hms.models.enums import (
    BookingStatus,
    NotificationType,
    PaymentMethod,
    RoomStatus,
    RoomStyle,
)
from hms.models.guest import Guest
from hms.models.hotel import Hotel
from hms.models.invoice import Invoice
from hms.models.notification import Notification
from hms.models.room import Room
from hms.models.room_booking import RoomBooking
from hms.models.room_key import RoomKey
from hms.staff.staff import Housekeeper, Manager, Receptionist, Staff


class PersistenceStore(Protocol):
    def save(self, system: HotelSystem) -> None: ...


class HotelSystem:
    """Central facade for the Hotel Management System (acts as the System actor)."""

    def __init__(
        self, hotel: Hotel, store: PersistenceStore | None = None
    ) -> None:
        self._hotel = hotel
        self._guests: dict[str, Guest] = {}
        self._bookings: dict[str, RoomBooking] = {}
        self._invoices: dict[str, Invoice] = {}
        self._staff: dict[str, Staff] = {}
        self._notifications: list[Notification] = []
        self._store = store
        self._persist_enabled = True

    @property
    def hotel(self) -> Hotel:
        return self._hotel

    @property
    def notifications(self) -> list[Notification]:
        return list(self._notifications)

    @property
    def guests(self) -> list[Guest]:
        return list(self._guests.values())

    def set_store(self, store: PersistenceStore | None) -> None:
        self._store = store

    def save(self) -> None:
        """Persist current state when a store is configured."""
        if self._store and self._persist_enabled:
            self._store.save(self)

    # ── Hydration helpers (used by SqliteStore) ─────────────────────────────

    def import_staff(self, member: Staff) -> None:
        self._staff[member.staff_id] = member

    def import_booking(self, booking: RoomBooking) -> None:
        self._bookings[booking.booking_id] = booking

    def import_invoice(self, invoice: Invoice) -> None:
        self._invoices[invoice.invoice_id] = invoice

    def import_notification(self, note: Notification) -> None:
        self._notifications.append(note)

    # ── Guests ──────────────────────────────────────────────────────────────

    def register_guest(self, name: str, email: str, phone: str = "") -> Guest:
        guest = Guest(name, email, phone)
        self._guests[guest.email] = guest
        self.save()
        return guest

    def get_guest(self, email: str) -> Guest:
        key = email.lower().strip()
        if key not in self._guests:
            raise KeyError(f"Guest {email} not found. Register them first.")
        return self._guests[key]

    def ensure_guest(self, name: str, email: str, phone: str = "") -> Guest:
        key = email.lower().strip()
        if key in self._guests:
            return self._guests[key]
        return self.register_guest(name, email, phone)

    # ── Room search & booking (FR-01..FR-05) ────────────────────────────────

    def search_rooms(
        self,
        check_in: date,
        check_out: date,
        style: RoomStyle | None = None,
        max_price: float | None = None,
    ) -> list[Room]:
        if check_out <= check_in:
            raise ValueError("Check-out must be after check-in.")
        available: list[Room] = []
        for room in self._hotel.rooms:
            if room.status == RoomStatus.MAINTENANCE:
                continue
            if not room.matches_filter(style=style, max_price=max_price):
                continue
            if self._is_room_free(room.number, check_in, check_out):
                available.append(room)
        return available

    def _is_room_free(self, room_number: str, check_in: date, check_out: date) -> bool:
        for booking in self._bookings.values():
            if booking.room_number != room_number:
                continue
            if booking.overlaps(check_in, check_out):
                return False
        return True

    def make_booking(
        self,
        room_number: str,
        guest_name: str,
        guest_email: str,
        check_in: date,
        check_out: date,
        phone: str = "",
    ) -> RoomBooking:
        room = self._hotel.get_room(room_number)
        if room.status == RoomStatus.MAINTENANCE:
            raise ValueError(f"Room {room_number} is under maintenance.")
        if not self._is_room_free(room_number, check_in, check_out):
            raise ValueError(
                f"Room {room_number} is not available for {check_in} → {check_out}."
            )
        guest = self.ensure_guest(guest_name, guest_email, phone)
        booking = RoomBooking(
            room_number=room.number,
            guest_email=guest.email,
            guest_name=guest.name,
            check_in=check_in,
            check_out=check_out,
            nightly_rate=room.price,
        )
        self._bookings[booking.booking_id] = booking
        self._send_notification(
            guest.email,
            f"Booking {booking.booking_id} confirmed for Room {room_number} "
            f"({check_in} to {check_out}).",
            NotificationType.BOOKING_CONFIRMATION,
        )
        self.save()
        return booking

    def cancel_booking(self, booking_id: str) -> RoomBooking:
        booking = self._get_booking(booking_id)
        booking.cancel()
        self._send_notification(
            booking.guest_email,
            f"Booking {booking.booking_id} has been cancelled.",
            NotificationType.CANCELLATION,
        )
        self.save()
        return booking

    # ── Check-in / Check-out (FR-06, FR-07, FR-17) ───────────────────────────

    def check_in(self, booking_id: str) -> tuple[RoomBooking, RoomKey]:
        booking = self._get_booking(booking_id)
        room = self._hotel.get_room(booking.room_number)
        if room.status in (RoomStatus.MAINTENANCE, RoomStatus.CLEANING):
            raise ValueError(
                f"Room {room.number} is not ready ({room.status.value})."
            )
        booking.check_in_guest()
        key = room.issue_key()
        room.set_status(RoomStatus.OCCUPIED)
        self.save()
        return booking, key

    def check_out(self, booking_id: str) -> Invoice:
        booking = self._get_booking(booking_id)
        room = self._hotel.get_room(booking.room_number)
        booking.check_out_guest()
        room.revoke_key()
        room.set_status(RoomStatus.CLEANING)
        invoice = self.generate_invoice(booking_id)
        self.save()
        return invoice

    # ── Housekeeping (FR-09, FR-10) ─────────────────────────────────────────

    def log_housekeeping(
        self,
        room_number: str,
        staff_name: str,
        activity: str,
        notes: str = "",
        set_status: RoomStatus | None = None,
        mark_cleaned: bool = False,
    ) -> str:
        room = self._hotel.get_room(room_number)
        entry = room.housekeeping.add_log(
            staff_name, activity, notes, mark_cleaned=mark_cleaned
        )
        if set_status is not None:
            room.set_status(set_status)
        self.save()
        return str(entry)

    # ── Room service & billing (FR-11..FR-13) ───────────────────────────────

    def request_room_service(
        self, booking_id: str, description: str, amount: float
    ):
        booking = self._get_booking(booking_id)
        charge = booking.add_charge(description, amount)
        self.save()
        return charge

    def generate_invoice(self, booking_id: str) -> Invoice:
        booking = self._get_booking(booking_id)
        for inv in self._invoices.values():
            if inv.booking_id == booking_id:
                return inv

        invoice = Invoice(booking.booking_id, booking.guest_email)
        invoice.add_line_item(
            f"Room {booking.room_number} × {booking.nights} night(s)",
            booking.room_cost,
        )
        for charge in booking.charges:
            invoice.add_room_charge(charge)
        self._invoices[invoice.invoice_id] = invoice
        self._send_notification(
            booking.guest_email,
            f"Invoice {invoice.invoice_id} generated. Total: R{invoice.total_amount:.2f}",
            NotificationType.BILLING,
        )
        self.save()
        return invoice

    def pay_invoice(self, invoice_id: str, method: PaymentMethod) -> Invoice:
        invoice = self._get_invoice(invoice_id)
        invoice.mark_paid(method)
        self._send_notification(
            invoice.guest_email,
            f"Payment received for Invoice {invoice.invoice_id} "
            f"via {method.value}. Amount: R{invoice.total_amount:.2f}",
            NotificationType.PAYMENT,
        )
        self.save()
        return invoice

    # ── Staff management (FR-15, FR-16) ─────────────────────────────────────

    def add_staff(self, role: str, name: str, email: str) -> Staff:
        role_key = role.strip().lower()
        factories = {
            "receptionist": Receptionist,
            "housekeeper": Housekeeper,
            "manager": Manager,
        }
        if role_key not in factories:
            raise ValueError(
                f"Unknown role '{role}'. Use: Receptionist, Housekeeper, Manager."
            )
        member = factories[role_key](name, email)
        self._staff[member.staff_id] = member
        self.save()
        return member

    def assign_staff(self, staff_id: str, assignment: str) -> Staff:
        member = self._get_staff(staff_id)
        member.set_assignment(assignment)
        self.save()
        return member

    def list_staff(self) -> list[Staff]:
        return list(self._staff.values())

    def perform_all_duties(self) -> list[str]:
        """Polymorphism demo — same call, different behaviour per role."""
        return [s.perform_duty() for s in self._staff.values() if s.active]

    # ── Lookups / listings ──────────────────────────────────────────────────

    def list_bookings(
        self, status: BookingStatus | None = None
    ) -> list[RoomBooking]:
        bookings = list(self._bookings.values())
        if status is not None:
            bookings = [b for b in bookings if b.booking_status == status]
        return bookings

    def list_invoices(self) -> list[Invoice]:
        return list(self._invoices.values())

    def get_booking(self, booking_id: str) -> RoomBooking:
        return self._get_booking(booking_id)

    # ── Internal helpers ────────────────────────────────────────────────────

    def _get_booking(self, booking_id: str) -> RoomBooking:
        key = booking_id.upper().strip()
        if key not in self._bookings:
            raise KeyError(f"Booking {booking_id} not found.")
        return self._bookings[key]

    def _get_invoice(self, invoice_id: str) -> Invoice:
        key = invoice_id.upper().strip()
        if key not in self._invoices:
            raise KeyError(f"Invoice {invoice_id} not found.")
        return self._invoices[key]

    def _get_staff(self, staff_id: str) -> Staff:
        key = staff_id.upper().strip()
        if key not in self._staff:
            raise KeyError(f"Staff {staff_id} not found.")
        return self._staff[key]

    def _send_notification(
        self, recipient: str, message: str, ntype: NotificationType
    ) -> Notification:
        """System actor auto-sends notifications (FR-14) — not manually initiated."""
        note = Notification(recipient, message, ntype)
        self._notifications.append(note)
        return note
