"""Notification — alerts sent to guests on system events."""

from __future__ import annotations

from datetime import datetime

from hms.models.enums import NotificationType


class Notification:
    def __init__(
        self, recipient: str, message: str, notification_type: NotificationType
    ) -> None:
        self._recipient = recipient
        self._message = message
        self._type = notification_type
        self._timestamp = datetime.now()

    @property
    def recipient(self) -> str:
        return self._recipient

    @property
    def message(self) -> str:
        return self._message

    @property
    def type(self) -> NotificationType:
        return self._type

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    @classmethod
    def restore(
        cls,
        recipient: str,
        message: str,
        notification_type: NotificationType,
        timestamp: datetime,
    ) -> Notification:
        note = cls(recipient, message, notification_type)
        note._timestamp = timestamp
        return note

    def __str__(self) -> str:
        return (
            f"[{self._timestamp.strftime('%Y-%m-%d %H:%M')}] "
            f"{self._type.value} → {self._recipient}: {self._message}"
        )
