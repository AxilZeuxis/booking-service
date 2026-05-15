from __future__ import annotations

from datetime import datetime, time, timedelta

from app.exceptions import DomainError, ErrorCodes
from app.holidays import COLOMBIA_HOLIDAYS_2026
from app.models import BOGOTA_TZ, Booking, BookingStatus, Service, User, UserPlan, ensure_bogota_datetime


OPENING_TIME = time(7, 0)
CLOSING_TIME = time(19, 0)
MINIMUM_ADVANCE = timedelta(hours=2)
MAX_ACTIVE_FUTURE_BOOKINGS = 3


def calculate_end_at(start_at: datetime, service: Service) -> datetime:
    return ensure_bogota_datetime(start_at) + timedelta(minutes=service.duration_minutes)


def validate_booking_creation(
    *,
    user: User,
    service: Service,
    start_at: datetime,
    bookings: list[Booking],
    services_by_id: dict[str, Service],
    now: datetime,
) -> datetime:
    now = ensure_bogota_datetime(now)
    start_at = ensure_bogota_datetime(start_at)
    end_at = calculate_end_at(start_at, service)

    _validate_business_day_and_hours(start_at, end_at)
    _validate_minimum_advance(start_at, now)
    _validate_user_booking_limit(user, bookings, now)
    _validate_professional_overlap(service, start_at, end_at, bookings, services_by_id)

    return end_at


def calculate_refund_percentage(*, user: User, service: Service, booking: Booking, now: datetime) -> int:
    if service.non_refundable:
        return 0

    now = ensure_bogota_datetime(now)
    start_at = ensure_bogota_datetime(booking.start_at)
    hours_before = (start_at - now).total_seconds() / 3600

    if user.plan == UserPlan.PREMIUM:
        if hours_before >= 4:
            return 100
        if hours_before >= 1:
            return 50
        return 0

    if hours_before > 24:
        return 100
    if hours_before >= 4:
        return 50
    return 0


def calculate_cancellation_amounts(
    *,
    user: User,
    service: Service,
    booking: Booking,
    now: datetime,
) -> tuple[int, int, int]:
    refund_percentage = calculate_refund_percentage(user=user, service=service, booking=booking, now=now)
    refund_amount_cents = service.price_cents * refund_percentage // 100
    charged_amount_cents = service.price_cents - refund_amount_cents
    return refund_percentage, refund_amount_cents, charged_amount_cents


def ensure_booking_can_be_cancelled(booking: Booking) -> None:
    if booking.status == BookingStatus.CANCELLED:
        raise DomainError(
            ErrorCodes.BOOKING_ALREADY_CANCELLED,
            "La reserva ya estaba cancelada.",
        )


def _validate_business_day_and_hours(start_at: datetime, end_at: datetime) -> None:
    if start_at.weekday() == 6:
        raise DomainError(
            ErrorCodes.OUTSIDE_BUSINESS_HOURS,
            "No se aceptan reservas los domingos.",
        )

    if start_at.date() in COLOMBIA_HOLIDAYS_2026:
        raise DomainError(
            ErrorCodes.HOLIDAY_NOT_ALLOWED,
            "No se aceptan reservas en festivos de Colombia 2026.",
        )

    if start_at.date() != end_at.date():
        raise DomainError(
            ErrorCodes.OUTSIDE_BUSINESS_HOURS,
            "La reserva debe empezar y terminar el mismo día dentro del horario de operación.",
        )

    if start_at.time() < OPENING_TIME or end_at.time() > CLOSING_TIME:
        raise DomainError(
            ErrorCodes.OUTSIDE_BUSINESS_HOURS,
            "La reserva debe estar entre lunes y sábado de 7:00 a 19:00 hora Bogotá.",
        )


def _validate_minimum_advance(start_at: datetime, now: datetime) -> None:
    if start_at - now < MINIMUM_ADVANCE:
        raise DomainError(
            ErrorCodes.INSUFFICIENT_ADVANCE,
            "La reserva debe crearse al menos con 2 horas de anticipación.",
        )


def _validate_user_booking_limit(user: User, bookings: list[Booking], now: datetime) -> None:
    active_future_count = sum(
        1
        for booking in bookings
        if booking.user_id == user.id
        and booking.status == BookingStatus.ACTIVE
        and ensure_bogota_datetime(booking.start_at) > now
    )

    if active_future_count >= MAX_ACTIVE_FUTURE_BOOKINGS:
        raise DomainError(
            ErrorCodes.USER_BOOKING_LIMIT,
            "El usuario no puede tener más de 3 reservas activas y futuras.",
        )


def _validate_professional_overlap(
    service: Service,
    start_at: datetime,
    end_at: datetime,
    bookings: list[Booking],
    services_by_id: dict[str, Service],
) -> None:
    for booking in bookings:
        if booking.status != BookingStatus.ACTIVE:
            continue

        booked_service = services_by_id.get(booking.service_id)
        if booked_service is None or booked_service.professional_id != service.professional_id:
            continue

        if start_at < booking.end_at and booking.start_at < end_at:
            raise DomainError(
                ErrorCodes.PROFESSIONAL_OVERLAP,
                "El profesional ya tiene una reserva activa que se solapa con ese horario.",
            )

