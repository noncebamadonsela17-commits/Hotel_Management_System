"""SQLite persistence for HotelSystem state."""

from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime
from pathlib import Path

from hms.models.enums import (
    BookingStatus,
    NotificationType,
    PaymentMethod,
    PaymentStatus,
    RoomStatus,
    RoomStyle,
)
from hms.models.guest import Guest
from hms.models.hotel import Hotel
from hms.models.housekeeping import LogEntry
from hms.models.invoice import Invoice
from hms.models.notification import Notification
from hms.models.room import Room
from hms.models.room_booking import RoomBooking
from hms.models.room_charge import RoomCharge
from hms.models.room_key import RoomKey
from hms.services.hotel_system import HotelSystem
from hms.staff.staff import Housekeeper, Manager, Receptionist, Staff


ROLE_MAP: dict[str, type[Staff]] = {
    "Receptionist": Receptionist,
    "Housekeeper": Housekeeper,
    "Manager": Manager,
}


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


class SqliteStore:
    """Save and load the full hotel system to a local SQLite file."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS hotel (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    name TEXT NOT NULL,
                    address TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS rooms (
                    number TEXT PRIMARY KEY,
                    style TEXT NOT NULL,
                    status TEXT NOT NULL,
                    price REAL NOT NULL,
                    capacity INTEGER NOT NULL,
                    amenities TEXT NOT NULL,
                    key_id TEXT,
                    key_barcode TEXT
                );

                CREATE TABLE IF NOT EXISTS housekeeping_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    room_number TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    staff_name TEXT NOT NULL,
                    activity TEXT NOT NULL,
                    notes TEXT NOT NULL,
                    FOREIGN KEY (room_number) REFERENCES rooms(number)
                );

                CREATE TABLE IF NOT EXISTS room_last_cleaned (
                    room_number TEXT PRIMARY KEY,
                    last_cleaned TEXT,
                    FOREIGN KEY (room_number) REFERENCES rooms(number)
                );

                CREATE TABLE IF NOT EXISTS guests (
                    email TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS staff (
                    staff_id TEXT PRIMARY KEY,
                    role TEXT NOT NULL,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    assignment TEXT NOT NULL,
                    active INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS bookings (
                    booking_id TEXT PRIMARY KEY,
                    room_number TEXT NOT NULL,
                    guest_email TEXT NOT NULL,
                    guest_name TEXT NOT NULL,
                    check_in TEXT NOT NULL,
                    check_out TEXT NOT NULL,
                    nightly_rate REAL NOT NULL,
                    status TEXT NOT NULL,
                    FOREIGN KEY (room_number) REFERENCES rooms(number)
                );

                CREATE TABLE IF NOT EXISTS room_charges (
                    charge_id TEXT PRIMARY KEY,
                    booking_id TEXT NOT NULL,
                    description TEXT NOT NULL,
                    amount REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (booking_id) REFERENCES bookings(booking_id)
                );

                CREATE TABLE IF NOT EXISTS invoices (
                    invoice_id TEXT PRIMARY KEY,
                    booking_id TEXT NOT NULL,
                    guest_email TEXT NOT NULL,
                    payment_status TEXT NOT NULL,
                    payment_method TEXT,
                    created_at TEXT NOT NULL,
                    paid_at TEXT,
                    FOREIGN KEY (booking_id) REFERENCES bookings(booking_id)
                );

                CREATE TABLE IF NOT EXISTS invoice_lines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_id TEXT NOT NULL,
                    description TEXT NOT NULL,
                    amount REAL NOT NULL,
                    line_order INTEGER NOT NULL,
                    FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id)
                );

                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recipient TEXT NOT NULL,
                    message TEXT NOT NULL,
                    type TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                );
                """
            )

    def exists_with_data(self) -> bool:
        if not self.db_path.exists():
            return False
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS c FROM hotel").fetchone()
            return bool(row and row["c"] > 0)

    def save(self, system: HotelSystem) -> None:
        hotel = system.hotel
        with self._connect() as conn:
            conn.execute("DELETE FROM invoice_lines")
            conn.execute("DELETE FROM invoices")
            conn.execute("DELETE FROM room_charges")
            conn.execute("DELETE FROM bookings")
            conn.execute("DELETE FROM notifications")
            conn.execute("DELETE FROM housekeeping_logs")
            conn.execute("DELETE FROM room_last_cleaned")
            conn.execute("DELETE FROM rooms")
            conn.execute("DELETE FROM guests")
            conn.execute("DELETE FROM staff")
            conn.execute("DELETE FROM hotel")

            conn.execute(
                "INSERT INTO hotel (id, name, address) VALUES (1, ?, ?)",
                (hotel.name, hotel.address),
            )

            for room in hotel.rooms:
                key = room.room_key
                conn.execute(
                    """
                    INSERT INTO rooms
                    (number, style, status, price, capacity, amenities, key_id, key_barcode)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        room.number,
                        room.style.value,
                        room.status.value,
                        room.price,
                        room.capacity,
                        json.dumps(room.amenities),
                        key.key_id if key else None,
                        key.barcode if key else None,
                    ),
                )
                last = room.housekeeping.last_cleaned
                conn.execute(
                    "INSERT INTO room_last_cleaned (room_number, last_cleaned) VALUES (?, ?)",
                    (room.number, last.isoformat() if last else None),
                )
                for entry in room.housekeeping.log_entries:
                    conn.execute(
                        """
                        INSERT INTO housekeeping_logs
                        (room_number, timestamp, staff_name, activity, notes)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            room.number,
                            entry.timestamp.isoformat(),
                            entry.staff_name,
                            entry.activity,
                            entry.notes,
                        ),
                    )

            for guest in system.guests:
                conn.execute(
                    "INSERT INTO guests (email, name, phone) VALUES (?, ?, ?)",
                    (guest.email, guest.name, guest.phone),
                )

            for member in system.list_staff():
                conn.execute(
                    """
                    INSERT INTO staff (staff_id, role, name, email, assignment, active)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        member.staff_id,
                        member.role(),
                        member.name,
                        member.email,
                        member.assignment,
                        1 if member.active else 0,
                    ),
                )

            for booking in system.list_bookings():
                conn.execute(
                    """
                    INSERT INTO bookings
                    (booking_id, room_number, guest_email, guest_name,
                     check_in, check_out, nightly_rate, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        booking.booking_id,
                        booking.room_number,
                        booking.guest_email,
                        booking.guest_name,
                        booking.check_in.isoformat(),
                        booking.check_out.isoformat(),
                        booking.nightly_rate,
                        booking.booking_status.value,
                    ),
                )
                for charge in booking.charges:
                    conn.execute(
                        """
                        INSERT INTO room_charges
                        (charge_id, booking_id, description, amount, timestamp)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            charge.charge_id,
                            booking.booking_id,
                            charge.description,
                            charge.amount,
                            charge.timestamp.isoformat(),
                        ),
                    )

            for invoice in system.list_invoices():
                conn.execute(
                    """
                    INSERT INTO invoices
                    (invoice_id, booking_id, guest_email, payment_status,
                     payment_method, created_at, paid_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        invoice.invoice_id,
                        invoice.booking_id,
                        invoice.guest_email,
                        invoice.payment_status.value,
                        invoice.payment_method.value if invoice.payment_method else None,
                        invoice.created_at.isoformat(),
                        invoice.paid_at.isoformat() if invoice.paid_at else None,
                    ),
                )
                for order, (desc, amount) in enumerate(invoice.line_items):
                    conn.execute(
                        """
                        INSERT INTO invoice_lines
                        (invoice_id, description, amount, line_order)
                        VALUES (?, ?, ?, ?)
                        """,
                        (invoice.invoice_id, desc, amount, order),
                    )

            for note in system.notifications:
                conn.execute(
                    """
                    INSERT INTO notifications (recipient, message, type, timestamp)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        note.recipient,
                        note.message,
                        note.type.value,
                        note.timestamp.isoformat(),
                    ),
                )

            conn.commit()

    def load(self) -> HotelSystem:
        with self._connect() as conn:
            hotel_row = conn.execute("SELECT * FROM hotel WHERE id = 1").fetchone()
            if hotel_row is None:
                raise FileNotFoundError(f"No hotel data in {self.db_path}")

            hotel = Hotel(hotel_row["name"], hotel_row["address"])

            for row in conn.execute("SELECT * FROM rooms ORDER BY number"):
                room = Room(
                    row["number"],
                    RoomStyle(row["style"]),
                    row["price"],
                    row["capacity"],
                    json.loads(row["amenities"]),
                )
                room.set_status(RoomStatus(row["status"]))
                if row["key_id"] and row["key_barcode"]:
                    room.attach_key(
                        RoomKey.restore(row["key_id"], row["key_barcode"], row["number"])
                    )
                hotel.add_room(room)

            for row in conn.execute(
                "SELECT * FROM housekeeping_logs ORDER BY id"
            ):
                room = hotel.get_room(row["room_number"])
                entry = LogEntry(
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    staff_name=row["staff_name"],
                    activity=row["activity"],
                    notes=row["notes"],
                )
                room.housekeeping.restore_entry(entry)

            for row in conn.execute("SELECT * FROM room_last_cleaned"):
                room = hotel.get_room(row["room_number"])
                room.housekeeping.set_last_cleaned(_parse_dt(row["last_cleaned"]))

            system = HotelSystem(hotel, store=self)
            system._persist_enabled = False

            for row in conn.execute("SELECT * FROM guests"):
                system.register_guest(row["name"], row["email"], row["phone"])

            for row in conn.execute("SELECT * FROM staff"):
                cls = ROLE_MAP[row["role"]]
                member = cls(row["name"], row["email"])
                member._apply_persisted_state(
                    row["staff_id"], row["assignment"], bool(row["active"])
                )
                system.import_staff(member)

            for row in conn.execute("SELECT * FROM bookings"):
                charges: list[RoomCharge] = []
                for c in conn.execute(
                    "SELECT * FROM room_charges WHERE booking_id = ?",
                    (row["booking_id"],),
                ):
                    charges.append(
                        RoomCharge.restore(
                            c["charge_id"],
                            c["description"],
                            c["amount"],
                            datetime.fromisoformat(c["timestamp"]),
                        )
                    )
                booking = RoomBooking.restore(
                    booking_id=row["booking_id"],
                    room_number=row["room_number"],
                    guest_email=row["guest_email"],
                    guest_name=row["guest_name"],
                    check_in=_parse_date(row["check_in"]),
                    check_out=_parse_date(row["check_out"]),
                    nightly_rate=row["nightly_rate"],
                    status=BookingStatus(row["status"]),
                    charges=charges,
                )
                system.import_booking(booking)

            for row in conn.execute("SELECT * FROM invoices"):
                lines = [
                    (line["description"], line["amount"])
                    for line in conn.execute(
                        """
                        SELECT description, amount FROM invoice_lines
                        WHERE invoice_id = ? ORDER BY line_order
                        """,
                        (row["invoice_id"],),
                    )
                ]
                method = (
                    PaymentMethod(row["payment_method"])
                    if row["payment_method"]
                    else None
                )
                invoice = Invoice.restore(
                    invoice_id=row["invoice_id"],
                    booking_id=row["booking_id"],
                    guest_email=row["guest_email"],
                    line_items=lines,
                    payment_status=PaymentStatus(row["payment_status"]),
                    payment_method=method,
                    created_at=datetime.fromisoformat(row["created_at"]),
                    paid_at=_parse_dt(row["paid_at"]),
                )
                system.import_invoice(invoice)

            for row in conn.execute("SELECT * FROM notifications ORDER BY id"):
                note = Notification.restore(
                    row["recipient"],
                    row["message"],
                    NotificationType(row["type"]),
                    datetime.fromisoformat(row["timestamp"]),
                )
                system.import_notification(note)

            system._persist_enabled = True
            return system
