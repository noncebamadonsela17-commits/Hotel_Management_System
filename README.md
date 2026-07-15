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

## Push this project to GitHub (3-week plan)

Use this plan so your repo looks active and intentional — small weekly commits beat one giant dump.

### Week 1 — Publish the foundation

**Goal:** Repo live on GitHub with a clear README.

1. Create an empty repo on GitHub named `Hotel_Management_System` (do **not** add a README there if you already have one locally).
2. In this project folder:

```bash
cd /home/wethinkcode/Music/Hotel_Management_System
git init
git add .
git status
git commit -m "$(cat <<'EOF'
Initial Hotel Management System with CLI, SQLite, and tests.

EOF
)"
git branch -M main
git remote add origin https://github.com/<your-username>/Hotel_Management_System.git
git push -u origin main
```

3. On GitHub: add a short description, topics (`python`, `oop`, `sqlite`, `cli`), and confirm the README renders.
4. Optional commit later in the week: fix typos in README or add a screenshot of the CLI.

### Week 2 — Prove quality

**Goal:** Show tests and a polished contribution story.

Suggested commits (one idea per day/session):

| Day idea | Example commit focus |
|----------|----------------------|
| Tests | Add edge-case tests (invalid dates, empty invoice pay) |
| UX | Friendlier date validation messages in the CLI |
| Docs | Add a `/docs` folder with a simple class diagram (PNG/Mermaid) |
| Demo | Record a 30–60s terminal GIF and link it in the README |

```bash
# after each small change
git add -A
git commit -m "Describe why you changed this"
git push
```

### Week 3 — Stretch feature + wrap-up

**Goal:** One visible upgrade so the repo doesn’t look abandoned.

Pick **one**:

- Export invoices to a text/PDF file  
- Simple FastAPI JSON endpoints for bookings  
- Login / role selection with a password stub  
- More room types or a booking conflict report  

Then:

1. Merge work into `main` with a clear commit message.  
2. Create a GitHub Release `v1.0.0` summarizing features.  
3. Pin the repo on your GitHub profile.  

### Commit message tips

- Prefer: `Add SQLite persistence so bookings survive restart`  
- Avoid: `update`, `fixes`, `stuff`  
- Keep commits small and runnable (`pytest` should pass after each push)

### Safety checklist before every push

```bash
pytest -v
git status
git push
```

Never commit `data/hotel.db`, `.venv/`, or `__pycache__/` — they are already listed in `.gitignore`.

---

## License

Personal / portfolio project. Add a `LICENSE` file (e.g. MIT) if you want to open-source it formally.
