# Hotel Management System

A Python object-oriented hotel operations CLI that manages room bookings, check-in/check-out, housekeeping, billing, staff, and guest notifications.

Data is saved automatically to a local **SQLite** database so bookings and invoices survive app restarts.

Based on the domain design in [`Hotel_Management_System_SRS.pdf`](Hotel_Management_System_SRS.pdf).

---

## Features

| Area | What you can do |
|------|-----------------|
| **Rooms** | Four types — Standard, Deluxe, Family, Business Suite — search by date, type, and price |
| **Bookings** | Guests and receptionists create bookings; guests can cancel |
| **Front desk** | Check-in (issues a `RoomKey`), check-out (generates an invoice) |
| **Housekeeping** | Per-room cleaning / maintenance logs and status updates |
| **Billing** | Room service charges, itemised invoices, pay by credit card / cheque / cash |
| **Notifications** | Automatic alerts on booking, cancellation, billing, and payment |
| **Staff** | Managers add and assign Receptionists, Housekeepers, and Managers |
| **Persistence** | SQLite auto-save after each action (`data/hotel.db`) |

### OOP principles used

- **Encapsulation** — booking status and invoice totals change only through class methods  
- **Abstraction** — `Staff` defines shared behaviour; roles hide implementation details  
- **Inheritance** — `Receptionist`, `Housekeeper`, and `Manager` extend `Staff`  
- **Polymorphism** — `perform_duty()` behaves differently per staff role  

---

## Requirements

- **Python 3.10 or newer**
- Stdlib only to run the app (`sqlite3` included)
- `pytest` for tests (optional)

Check your version:

```bash
python3 --version
```

---

## How to run

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/Hotel_Management_System.git
cd Hotel_Management_System
```

Replace `<your-username>` with your GitHub username.

### 2. (Optional) Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt  # only needed for tests
```

### 3. Start the app

```bash
python3 main.py
```

On first run, demo data is created and saved to `data/hotel.db`.  
Later runs reload that file so your bookings stay available.

### 4. Choose a role

| Key | Role | Typical actions |
|-----|------|-----------------|
| `1` | Guest | Search rooms, book, cancel, room service, pay bill |
| `2` | Receptionist | Walk-in bookings, check-in/out, manage rooms, payments |
| `3` | Housekeeper | Log cleaning/maintenance, mark rooms available |
| `4` | Manager | Add/assign staff, occupancy, notifications |
| `0` | Exit | Quit |

Dates use **`YYYY-MM-DD`** (example: `2026-07-20`).

### Reset demo data

```bash
rm -rf data/hotel.db
python3 main.py
```

---

## Run tests

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -v
```

---

## Quick demo walkthrough

1. **Guest** → Search rooms → Make a booking → copy the **Booking ID**  
2. **Receptionist** → Check in with that ID → note the **RoomKey**  
3. **Guest** → Request room service on the same booking  
4. **Receptionist** → Check out → pay the **Invoice ID**  
5. **Manager** → View occupancy and notifications  
6. Quit and run `python3 main.py` again — your data is still there  

---

## Project structure

```
Hotel_Management_System/
├── Hotel_Management_System_SRS.pdf
├── main.py                  # CLI entry point
├── requirements.txt         # pytest (for development)
├── README.md
├── data/                    # created at runtime (gitignored)
│   └── hotel.db
├── tests/
│   └── test_hotel_system.py
└── hms/
    ├── models/              # Hotel, Room, Booking, Invoice, …
    ├── staff/               # Staff ABC + role subclasses
    ├── services/            # HotelSystem facade
    ├── persistence/         # SQLite save/load
    └── seed.py              # Demo data + load_or_create
```

---


