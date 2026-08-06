"""Staff hierarchy — abstract Staff with role-specific subclasses."""

from __future__ import annotations

from abc import ABC, abstractmethod
import uuid


class Staff(ABC):
    """Abstract base for all hotel staff — demonstrates abstraction & inheritance."""

    def __init__(self, name: str, email: str) -> None:
        self._staff_id = str(uuid.uuid4())[:8].upper()
        self._name = name
        self._email = email.lower().strip()
        self._active = True
        self._assignment: str = "Unassigned"

    @property
    def staff_id(self) -> str:
        return self._staff_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def email(self) -> str:
        return self._email

    @property
    def active(self) -> bool:
        return self._active

    @property
    def assignment(self) -> str:
        return self._assignment

    def set_assignment(self, assignment: str) -> None:
        self._assignment = assignment

    def deactivate(self) -> None:
        self._active = False

    def activate(self) -> None:
        self._active = True

    def _apply_persisted_state(
        self, staff_id: str, assignment: str, active: bool
    ) -> None:
        self._staff_id = staff_id
        self._assignment = assignment
        self._active = active

    @abstractmethod
    def role(self) -> str:
        """Return the staff role name."""

    @abstractmethod
    def perform_duty(self) -> str:
        """Polymorphic duty — overridden by each subclass."""

    def __str__(self) -> str:
        status = "active" if self._active else "inactive"
        return (
            f"{self.role()} {self._name} ({self._staff_id}) | "
            f"{self._assignment} | {status}"
        )


class Receptionist(Staff):
    def role(self) -> str:
        return "Receptionist"

    def perform_duty(self) -> str:
        return f"{self._name} is handling front-desk check-ins and bookings."


class Housekeeper(Staff):
    def role(self) -> str:
        return "Housekeeper"

    def perform_duty(self) -> str:
        return f"{self._name} is cleaning and maintaining guest rooms."


class Manager(Staff):
    def role(self) -> str:
        return "Manager"

    def perform_duty(self) -> str:
        return f"{self._name} is overseeing staff and hotel operations."
