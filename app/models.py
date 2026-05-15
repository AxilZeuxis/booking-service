from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, field_validator


BOGOTA_TZ = ZoneInfo("America/Bogota")


class UserPlan(str, Enum):
    STANDARD = "standard"
    PREMIUM = "premium"


class BookingStatus(str, Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"


def ensure_bogota_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=BOGOTA_TZ)
    return value.astimezone(BOGOTA_TZ)


class User(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    plan: UserPlan = UserPlan.STANDARD


class Service(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    duration_minutes: int = Field(gt=0)
    professional_id: str
    price_cents: int = Field(ge=0)
    non_refundable: bool = False


class Booking(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    user_id: str
    service_id: str
    start_at: datetime
    end_at: datetime
    status: BookingStatus = BookingStatus.ACTIVE
    created_at: datetime
    cancelled_at: datetime | None = None
    refund_percentage: int | None = None
    refund_amount_cents: int | None = None
    charged_amount_cents: int | None = None

    @field_validator("start_at", "end_at", "created_at", "cancelled_at", mode="before")
    @classmethod
    def normalize_datetimes(cls, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, datetime):
            return ensure_bogota_datetime(value)
        return value

    @field_validator("start_at", "end_at", "created_at", "cancelled_at")
    @classmethod
    def ensure_timezone(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return ensure_bogota_datetime(value)


class CreateBookingRequest(BaseModel):
    user_id: str
    service_id: str
    start_at: datetime

    @field_validator("start_at")
    @classmethod
    def ensure_start_timezone(cls, value: datetime) -> datetime:
        return ensure_bogota_datetime(value)


class BookingResponse(BaseModel):
    id: str
    user_id: str
    service_id: str
    start_at: datetime
    end_at: datetime
    status: BookingStatus
    created_at: datetime
    cancelled_at: datetime | None = None
    refund_percentage: int | None = None
    refund_amount_cents: int | None = None
    charged_amount_cents: int | None = None


class CancellationResponse(BaseModel):
    id: str
    status: BookingStatus
    refund_percentage: int
    refund_amount_cents: int
    charged_amount_cents: int
    cancelled_at: datetime

