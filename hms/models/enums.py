"""Domain enums for the Hotel Management System."""

from enum import Enum


class RoomStyle(Enum):
    STANDARD = "Standard"
    DELUXE = "Deluxe"
    FAMILY = "Family"
    BUSINESS_SUITE = "Business Suite"


class RoomStatus(Enum):
    AVAILABLE = "Available"
    OCCUPIED = "Occupied"
    MAINTENANCE = "Maintenance"
    CLEANING = "Cleaning"


class BookingStatus(Enum):
    CONFIRMED = "Confirmed"
    CHECKED_IN = "Checked In"
    CHECKED_OUT = "Checked Out"
    CANCELLED = "Cancelled"


class PaymentMethod(Enum):
    CREDIT_CARD = "Credit Card"
    CHEQUE = "Cheque"
    CASH = "Cash"


class PaymentStatus(Enum):
    UNPAID = "Unpaid"
    PAID = "Paid"
    PARTIAL = "Partial"


class NotificationType(Enum):
    BOOKING_CONFIRMATION = "Booking Confirmation"
    CANCELLATION = "Cancellation"
    BILLING = "Billing"
    PAYMENT = "Payment"
