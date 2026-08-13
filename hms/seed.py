"""Seed sample hotel data for demos and testing."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from hms.models.enums import RoomStyle
from hms.models.hotel import Hotel
from hms.models.room import Room
from hms.persistence.sqlite_store import SqliteStore
from hms.services.hotel_system import HotelSystem

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "hotel.db"

DEFAULT_ROOMS: list[tuple[str, RoomStyle, float, int, list[str]]] = [
    ("101", RoomStyle.STANDARD, 850.0, 2, ["WiFi", "TV"]),
    ("102", RoomStyle.STANDARD, 850.0, 2, ["WiFi", "TV"]),
    ("201", RoomStyle.DELUXE, 1250.0, 2, ["WiFi", "TV", "Mini-bar", "Balcony"]),
    ("202", RoomStyle.DELUXE, 1300.0, 2, ["WiFi", "TV", "Mini-bar", "Sea view"]),
    ("301", RoomStyle.FAMILY, 1800.0, 4, ["WiFi", "TV", "Two beds", "Kitchenette"]),
    ("302", RoomStyle.FAMILY, 1800.0, 4, ["WiFi", "TV", "Two beds", "Kitchenette"]),
    ("401", RoomStyle.BUSINESS_SUITE, 2500.0, 2, ["WiFi", "Desk", "Meeting area", "Espresso"]),
    ("402", RoomStyle.BUSINESS_SUITE, 2600.0, 2, ["WiFi", "Desk", "Lounge", "Espresso"]),
]


def create_demo_system(store: SqliteStore | None = None) -> HotelSystem:
    """Build a fresh demo hotel. Pass a store to enable auto-persistence."""
    hotel = Hotel("Grand Cape Hotel", "1 Harbour Road, Cape Town")
    for number, style, price, capacity, amenities in DEFAULT_ROOMS:
        hotel.add_room(Room(number, style, price, capacity, amenities))

    system = HotelSystem(hotel, store=store)
    # Seed without writing mid-way; one final save at the end.
    system._persist_enabled = False

    system.add_staff("Manager", "Thabo Molefe", "thabo@grandcape.co.za")
    reception = system.add_staff("Receptionist", "Aisha Naidoo", "aisha@grandcape.co.za")
    housekeeper = system.add_staff(
        "Housekeeper", "Lerato Dlamini", "lerato@grandcape.co.za"
    )
    system.assign_staff(reception.staff_id, "Front Desk — Morning Shift")
    system.assign_staff(housekeeper.staff_id, "Floors 1–2")

    today = date.today()
    system.register_guest("Jordan Smith", "jordan@example.com", "0820001111")
    system.make_booking(
        "201",
        "Jordan Smith",
        "jordan@example.com",
        today + timedelta(days=1),
        today + timedelta(days=3),
    )

    system._persist_enabled = True
    system.save()
    return system


def load_or_create_system(db_path: Path | str = DEFAULT_DB_PATH) -> tuple[HotelSystem, bool]:
    """
    Load from SQLite if present; otherwise create demo data and save it.

    Returns (system, created_fresh).
    """
    store = SqliteStore(db_path)
    if store.exists_with_data():
        return store.load(), False
    return create_demo_system(store=store), True
