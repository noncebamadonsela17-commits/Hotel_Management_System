"""Guest — a hotel customer identified by email."""

from __future__ import annotations


class Guest:
    def __init__(self, name: str, email: str, phone: str = "") -> None:
        if not email or "@" not in email:
            raise ValueError("Guest must have a valid email.")
        self._name = name
        self._email = email.lower().strip()
        self._phone = phone

    @property
    def name(self) -> str:
        return self._name

    @property
    def email(self) -> str:
        return self._email

    @property
    def phone(self) -> str:
        return self._phone

    def __str__(self) -> str:
        return f"{self._name} <{self._email}>"
