"""Core behaviour and persistence tests for the Hotel Management System."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pytest

from hms.models.enums import PaymentMethod, RoomStatus, RoomStyle
from hms.persistence.sqlite_store import SqliteStore
from hms.seed import create_demo_system


@pytest.fixture
def system():
    return create_demo_system(store=None)


@pytest.fixture
def future_dates():
    start = date.today() + timedelta(days=10)
    end = start + timedelta(days=3)
    return start, end


def test_search_rooms_by_type_and_price(system, future_dates):
    check_in, check_out = future_dates
    rooms = system.search_rooms(
        check_in, check_out, style=RoomStyle.DELUXE, max_price=1500
    )
    assert rooms
    assert all(r.style == RoomStyle.DELUXE for r in rooms)
    assert all(r.price <= 1500 for r in rooms)


def test_make_booking_and_block_double_booking(system, future_dates):
    check_in, check_out = future_dates
    booking = system.make_booking(
        "101", "Ada Lovelace", "ada@example.com", check_in, check_out
    )
    assert booking.room_number == "101"

    with pytest.raises(ValueError, match="not available"):
        system.make_booking(
            "101", "Other Guest", "other@example.com", check_in, check_out
        )


def test_cancel_frees_room(system, future_dates):
    check_in, check_out = future_dates
    booking = system.make_booking(
        "102", "Cancel Me", "cancel@example.com", check_in, check_out
    )
    system.cancel_booking(booking.booking_id)
    rooms = system.search_rooms(check_in, check_out)
    assert any(r.number == "102" for r in rooms)


def test_check_in_issues_key_and_occupies_room(system, future_dates):
    check_in, check_out = future_dates
    booking = system.make_booking(
        "301", "Guest One", "g1@example.com", check_in, check_out
    )
    _, key = system.check_in(booking.booking_id)
    room = system.hotel.get_room("301")
    assert room.status == RoomStatus.OCCUPIED
    assert key.assigned_room == "301"
    assert room.room_key is not None


def test_room_service_checkout_invoice_and_payment(system, future_dates):
    check_in, check_out = future_dates
    booking = system.make_booking(
        "401", "Biz Guest", "biz@example.com", check_in, check_out
    )
    system.check_in(booking.booking_id)
    system.request_room_service(booking.booking_id, "Laundry", 150.0)

    invoice = system.check_out(booking.booking_id)
    assert invoice.total_amount == booking.room_cost + 150.0
    assert system.hotel.get_room("401").status == RoomStatus.CLEANING

    paid = system.pay_invoice(invoice.invoice_id, PaymentMethod.CASH)
    assert paid.payment_status.value == "Paid"


def test_cannot_cancel_after_check_in(system, future_dates):
    check_in, check_out = future_dates
    booking = system.make_booking(
        "202", "Locked", "locked@example.com", check_in, check_out
    )
    system.check_in(booking.booking_id)
    with pytest.raises(ValueError, match="checked in"):
        system.cancel_booking(booking.booking_id)


def test_housekeeping_marks_available(system):
    system.log_housekeeping(
        "101",
        "Lerato",
        "Deep clean",
        set_status=RoomStatus.AVAILABLE,
        mark_cleaned=True,
    )
    room = system.hotel.get_room("101")
    assert room.status == RoomStatus.AVAILABLE
    assert room.housekeeping.last_cleaned is not None
    assert room.housekeeping.log_entries


def test_staff_polymorphism(system):
    duties = system.perform_all_duties()
    assert len(duties) >= 3
    assert any("front-desk" in d for d in duties)
    assert any("cleaning" in d for d in duties)
    assert any("overseeing" in d for d in duties)


def test_sqlite_round_trip(tmp_path: Path, future_dates):
    db = tmp_path / "test.db"
    store = SqliteStore(db)
    system = create_demo_system(store=store)

    check_in, check_out = future_dates
    booking = system.make_booking(
        "102", "Persist Guest", "persist@example.com", check_in, check_out
    )
    system.check_in(booking.booking_id)
    booking_id = booking.booking_id

    reloaded = store.load()
    restored = reloaded.get_booking(booking_id)
    assert restored.guest_email == "persist@example.com"
    assert restored.booking_status.value == "Checked In"
    assert reloaded.hotel.get_room("102").status == RoomStatus.OCCUPIED
    assert len(reloaded.notifications) >= len(system.notifications)
