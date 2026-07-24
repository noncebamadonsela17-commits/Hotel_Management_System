"""Invoice — aggregates booking costs and room charges."""

from __future__ import annotations

import uuid
from datetime import datetime

from hms.models.enums import PaymentMethod, PaymentStatus
from hms.models.room_charge import RoomCharge


class Invoice:
    def __init__(self, booking_id: str, guest_email: str) -> None:
        self._invoice_id = str(uuid.uuid4())[:8].upper()
        self._booking_id = booking_id
        self._guest_email = guest_email
        self._line_items: list[tuple[str, float]] = []
        self._payment_status = PaymentStatus.UNPAID
        self._payment_method: PaymentMethod | None = None
        self._created_at = datetime.now()
        self._paid_at: datetime | None = None

    @property
    def invoice_id(self) -> str:
        return self._invoice_id

    @property
    def booking_id(self) -> str:
        return self._booking_id

    @property
    def guest_email(self) -> str:
        return self._guest_email

    @property
    def line_items(self) -> list[tuple[str, float]]:
        return list(self._line_items)

    @property
    def total_amount(self) -> float:
        return round(sum(amount for _, amount in self._line_items), 2)

    @property
    def payment_status(self) -> PaymentStatus:
        return self._payment_status

    @property
    def payment_method(self) -> PaymentMethod | None:
        return self._payment_method

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def paid_at(self) -> datetime | None:
        return self._paid_at

    @classmethod
    def restore(
        cls,
        invoice_id: str,
        booking_id: str,
        guest_email: str,
        line_items: list[tuple[str, float]],
        payment_status: PaymentStatus,
        payment_method: PaymentMethod | None,
        created_at: datetime,
        paid_at: datetime | None = None,
    ) -> Invoice:
        invoice = cls(booking_id, guest_email)
        invoice._invoice_id = invoice_id
        invoice._line_items = [(d, round(a, 2)) for d, a in line_items]
        invoice._payment_status = payment_status
        invoice._payment_method = payment_method
        invoice._created_at = created_at
        invoice._paid_at = paid_at
        return invoice

    def add_line_item(self, description: str, amount: float) -> None:
        if self._payment_status == PaymentStatus.PAID:
            raise ValueError("Cannot modify a paid invoice.")
        self._line_items.append((description, round(amount, 2)))

    def add_room_charge(self, charge: RoomCharge) -> None:
        self.add_line_item(charge.description, charge.amount)

    def mark_paid(self, method: PaymentMethod) -> None:
        if not self._line_items:
            raise ValueError("Cannot pay an empty invoice.")
        if self._payment_status == PaymentStatus.PAID:
            raise ValueError("Invoice is already paid.")
        self._payment_status = PaymentStatus.PAID
        self._payment_method = method
        self._paid_at = datetime.now()

    def summary(self) -> str:
        lines = [
            f"Invoice {self._invoice_id} (Booking {self._booking_id})",
            f"Guest: {self._guest_email}",
            f"Status: {self._payment_status.value}",
            "-" * 40,
        ]
        for desc, amount in self._line_items:
            lines.append(f"  {desc:<30} R{amount:>8.2f}")
        lines.append("-" * 40)
        lines.append(f"  {'TOTAL':<30} R{self.total_amount:>8.2f}")
        if self._payment_method:
            lines.append(f"  Paid via: {self._payment_method.value}")
        return "\n".join(lines)

    def __str__(self) -> str:
        return (
            f"Invoice({self._invoice_id}, total=R{self.total_amount:.2f}, "
            f"status={self._payment_status.value})"
        )
