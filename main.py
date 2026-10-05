"""Command-line front desk for the Hotel Management System."""

from __future__ import annotations

import sys
from collections.abc import Callable
from datetime import date
from pathlib import Path

from hms.models.enums import PaymentMethod, RoomStatus, RoomStyle
from hms.seed import DEFAULT_DB_PATH, load_or_create_system
from hms.services.hotel_system import HotelSystem


def prompt(label: str) -> str:
    try:
        return input(f"{label}: ").strip()
    except EOFError:
        print()
        raise SystemExit(0) from None


def prompt_date(label: str) -> date:
    while True:
        raw = prompt(f"{label} (YYYY-MM-DD)")
        try:
            return date.fromisoformat(raw)
        except ValueError:
            print("Enter a date as YYYY-MM-DD.")


def prompt_optional_amount(label: str) -> float | None:
    while True:
        raw = prompt(label)
        if raw == "":
            return None
        try:
            amount = float(raw)
        except ValueError:
            print("Enter a number, or leave blank.")
            continue
        if amount < 0:
            print("Amount cannot be negative.")
            continue
        return amount


def prompt_amount(label: str) -> float:
    while True:
        raw = prompt(label)
        try:
            amount = float(raw)
        except ValueError:
            print("Enter a number.")
            continue
        if amount < 0:
            print("Amount cannot be negative.")
            continue
        return amount


def choose(label: str, options: list, allow_blank: bool = False):
    print(label)
    for index, option in enumerate(options, start=1):
        name = option.value if hasattr(option, "value") else str(option)
        print(f"  {index}  {name}")
    if allow_blank:
        print("  blank  any")
    while True:
        raw = prompt("Choose")
        if allow_blank and raw == "":
            return None
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        print("Choose a number from the list.")


def run_menu(title: str, actions: dict[str, tuple[str, Callable[[], None]]]) -> None:
    while True:
        print(f"\n{title}")
        for key, (label, _) in actions.items():
            print(f"  {key}  {label}")
        print("  0  Back")
        choice = prompt("Choose")
        if choice == "0":
            return
        action = actions.get(choice)
        if action is None:
            print("Unknown option.")
            continue
        try:
            action[1]()
        except (ValueError, KeyError) as exc:
            print(exc)


def print_rooms(rooms) -> None:
    if not rooms:
        print("No rooms match.")
        return
    for room in rooms:
        print(f"  {room}")


def search_rooms(system: HotelSystem) -> None:
    check_in = prompt_date("Check in")
    check_out = prompt_date("Check out")
    style = choose("Room type", list(RoomStyle), allow_blank=True)
    max_price = prompt_optional_amount("Max price per night (blank for any)")
    rooms = system.search_rooms(check_in, check_out, style=style, max_price=max_price)
    print_rooms(rooms)


def make_booking(system: HotelSystem) -> None:
    print_rooms(system.hotel.rooms)
    room_number = prompt("Room number")
    name = prompt("Guest name")
    email = prompt("Guest email")
    phone = prompt("Phone (optional)")
    check_in = prompt_date("Check in")
    check_out = prompt_date("Check out")
    booking = system.make_booking(
        room_number, name, email, check_in, check_out, phone
    )
    print(booking)
    print(f"Booking ID: {booking.booking_id}")


def cancel_booking(system: HotelSystem) -> None:
    booking = system.cancel_booking(prompt("Booking ID"))
    print(booking)


def request_room_service(system: HotelSystem) -> None:
    booking_id = prompt("Booking ID")
    description = prompt("Description")
    amount = prompt_amount("Amount")
    charge = system.request_room_service(booking_id, description, amount)
    print(charge)


def pay_invoice(system: HotelSystem) -> None:
    invoice_id = prompt("Invoice ID")
    invoice = next(
        (item for item in system.list_invoices() if item.invoice_id == invoice_id.upper()),
        None,
    )
    if invoice is None:
        raise KeyError(f"Invoice {invoice_id} not found.")
    print(invoice.summary())
    method = choose("Payment method", list(PaymentMethod))
    paid = system.pay_invoice(invoice.invoice_id, method)
    print(paid.summary())


def check_in(system: HotelSystem) -> None:
    booking, key = system.check_in(prompt("Booking ID"))
    print(booking)
    print(f"Room key: {key}")


def check_out(system: HotelSystem) -> None:
    invoice = system.check_out(prompt("Booking ID"))
    print(invoice.summary())
    print(f"Invoice ID: {invoice.invoice_id}")


def list_bookings(system: HotelSystem) -> None:
    bookings = system.list_bookings()
    if not bookings:
        print("No bookings.")
        return
    for booking in bookings:
        print(f"  {booking}")


def update_room(system: HotelSystem) -> None:
    print_rooms(system.hotel.rooms)
    number = prompt("Room number")
    status = choose("New status (blank to leave)", list(RoomStatus), allow_blank=True)
    price = prompt_optional_amount("New price (blank to leave)")
    room = system.hotel.update_room(number, price=price, status=status)
    system.save()
    print(room)


def list_invoices(system: HotelSystem) -> None:
    invoices = system.list_invoices()
    if not invoices:
        print("No invoices.")
        return
    for invoice in invoices:
        print(f"  {invoice}")


def log_housekeeping(system: HotelSystem, mark_available: bool = False) -> None:
    print_rooms(system.hotel.rooms)
    room_number = prompt("Room number")
    staff_name = prompt("Your name")
    if mark_available:
        entry = system.log_housekeeping(
            room_number,
            staff_name,
            "Clean",
            notes="Marked available",
            set_status=RoomStatus.AVAILABLE,
            mark_cleaned=True,
        )
    else:
        activity = prompt("Activity")
        notes = prompt("Notes (optional)")
        status = choose("Set room status (blank to leave)", list(RoomStatus), allow_blank=True)
        entry = system.log_housekeeping(
            room_number,
            staff_name,
            activity,
            notes,
            set_status=status,
            mark_cleaned=False,
        )
    print(entry)


def show_occupancy(system: HotelSystem) -> None:
    print(system.hotel)
    for status, count in system.hotel.occupancy_report().items():
        print(f"  {status}: {count}")


def show_notifications(system: HotelSystem) -> None:
    notes = system.notifications
    if not notes:
        print("No notifications.")
        return
    for note in notes:
        print(f"  {note}")


def list_staff(system: HotelSystem) -> None:
    staff = system.list_staff()
    if not staff:
        print("No staff.")
        return
    for member in staff:
        print(f"  {member}")


def add_staff(system: HotelSystem) -> None:
    role = choose("Role", ["Receptionist", "Housekeeper", "Manager"])
    member = system.add_staff(role, prompt("Name"), prompt("Email"))
    print(member)


def assign_staff(system: HotelSystem) -> None:
    list_staff(system)
    member = system.assign_staff(prompt("Staff ID"), prompt("Assignment"))
    print(member)


def show_duties(system: HotelSystem) -> None:
    duties = system.perform_all_duties()
    if not duties:
        print("No active staff.")
        return
    for duty in duties:
        print(f"  {duty}")


def guest_menu(system: HotelSystem) -> None:
    run_menu(
        "Guest",
        {
            "1": ("Search rooms", lambda: search_rooms(system)),
            "2": ("Make a booking", lambda: make_booking(system)),
            "3": ("Cancel a booking", lambda: cancel_booking(system)),
            "4": ("Request room service", lambda: request_room_service(system)),
            "5": ("Pay a bill", lambda: pay_invoice(system)),
        },
    )


def receptionist_menu(system: HotelSystem) -> None:
    run_menu(
        "Receptionist",
        {
            "1": ("Search rooms", lambda: search_rooms(system)),
            "2": ("Walk-in booking", lambda: make_booking(system)),
            "3": ("Check in", lambda: check_in(system)),
            "4": ("Check out", lambda: check_out(system)),
            "5": ("List bookings", lambda: list_bookings(system)),
            "6": ("Update a room", lambda: update_room(system)),
            "7": ("Take a payment", lambda: pay_invoice(system)),
            "8": ("List invoices", lambda: list_invoices(system)),
        },
    )


def housekeeper_menu(system: HotelSystem) -> None:
    run_menu(
        "Housekeeper",
        {
            "1": ("List rooms", lambda: print_rooms(system.hotel.rooms)),
            "2": ("Log cleaning or maintenance", lambda: log_housekeeping(system)),
            "3": ("Mark a room available", lambda: log_housekeeping(system, mark_available=True)),
        },
    )


def manager_menu(system: HotelSystem) -> None:
    run_menu(
        "Manager",
        {
            "1": ("Occupancy", lambda: show_occupancy(system)),
            "2": ("Notifications", lambda: show_notifications(system)),
            "3": ("List staff", lambda: list_staff(system)),
            "4": ("Add staff", lambda: add_staff(system)),
            "5": ("Assign staff", lambda: assign_staff(system)),
            "6": ("Staff duties", lambda: show_duties(system)),
        },
    )


def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    db_path = Path(args[0]) if args else DEFAULT_DB_PATH
    system, created = load_or_create_system(db_path)
    if created:
        print(f"Created demo data for {system.hotel}.")
    else:
        print(f"Loaded {system.hotel}.")
    print(f"Database: {db_path}")

    menus = {
        "1": ("Guest", guest_menu),
        "2": ("Receptionist", receptionist_menu),
        "3": ("Housekeeper", housekeeper_menu),
        "4": ("Manager", manager_menu),
    }
    while True:
        print("\nSign in as")
        for key, (label, _) in menus.items():
            print(f"  {key}  {label}")
        print("  0  Exit")
        choice = prompt("Choose")
        if choice == "0":
            print("Goodbye.")
            return
        selected = menus.get(choice)
        if selected is None:
            print("Unknown option.")
            continue
        selected[1](system)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nGoodbye.")
