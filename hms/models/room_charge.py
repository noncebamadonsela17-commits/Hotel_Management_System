"""RoomCharge — a service/charge against a booking."""

from __future__ import annotations

import uuid
from datetime import datetime


class RoomCharge:
    def __init__(self, description: str, amount: float) -> None:
        if amount < 0:
            raise ValueError("Charge amount cannot be negative.")
        self._charge_id = str(uuid.uuid4())[:8].upper()
        self._description = description
        self._amount = round(amount, 2)
        self._timestamp = datetime.now()

    @property
    def charge_id(self) -> str:
        return self._charge_id

    @property
    def description(self) -> str:
        return self._description

    @property
    def amount(self) -> float:
        return self._amount

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    @classmethod
    def restore(
        cls,
        charge_id: str,
        description: str,
        amount: float,
        timestamp: datetime,
    ) -> RoomCharge:
        charge = cls(description, amount)
        charge._charge_id = charge_id
        charge._timestamp = timestamp
        return charge

    def __str__(self) -> str:
        return f"[{self._charge_id}] {self._description}: R{self._amount:.2f}"
