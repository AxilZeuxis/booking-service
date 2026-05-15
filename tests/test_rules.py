from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.models import Booking, BookingStatus, Service, User, UserPlan
from app.rules import calculate_cancellation_amounts, calculate_refund_percentage


BOGOTA_TZ = ZoneInfo("America/Bogota")
NOW = datetime(2026, 5, 15, 8, 0, tzinfo=BOGOTA_TZ)


def make_user(plan: UserPlan) -> User:
    return User(id="u-001", name="Test User", plan=plan)


def make_service(*, non_refundable: bool = False) -> Service:
    return Service(
        id="s-001",
        name="Consulta",
        duration_minutes=60,
        professional_id="p-001",
        price_cents=10000,
        non_refundable=non_refundable,
    )


def make_booking(hours_before: float) -> Booking:
    return Booking(
        id="b-001",
        user_id="u-001",
        service_id="s-001",
        start_at=NOW + timedelta(hours=hours_before),
        end_at=NOW + timedelta(hours=hours_before + 1),
        status=BookingStatus.ACTIVE,
        created_at=NOW,
    )


@pytest.mark.parametrize(
    ("hours_before", "expected"),
    [
        (25, 100),
        (24, 50),
        (4, 50),
        (3.99, 0),
    ],
)
def test_cancel_standard_user_refund_tiers(hours_before: float, expected: int) -> None:
    percentage = calculate_refund_percentage(
        user=make_user(UserPlan.STANDARD),
        service=make_service(),
        booking=make_booking(hours_before),
        now=NOW,
    )

    assert percentage == expected


@pytest.mark.parametrize(
    ("hours_before", "expected"),
    [
        (24, 100),
        (4, 100),
        (3.99, 50),
        (1, 50),
        (0.99, 0),
    ],
)
def test_cancel_premium_user_refund_tiers(hours_before: float, expected: int) -> None:
    percentage = calculate_refund_percentage(
        user=make_user(UserPlan.PREMIUM),
        service=make_service(),
        booking=make_booking(hours_before),
        now=NOW,
    )

    assert percentage == expected


def test_cancel_non_refundable_service_always_returns_zero() -> None:
    percentage, refund_amount, charged_amount = calculate_cancellation_amounts(
        user=make_user(UserPlan.PREMIUM),
        service=make_service(non_refundable=True),
        booking=make_booking(48),
        now=NOW,
    )

    assert percentage == 0
    assert refund_amount == 0
    assert charged_amount == 10000

