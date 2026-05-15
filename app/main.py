from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Annotated, Callable
from uuid import uuid4

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

from app.exceptions import DomainError, ErrorCodes
from app.models import (
    BOGOTA_TZ,
    Booking,
    BookingResponse,
    BookingStatus,
    CancellationResponse,
    CreateBookingRequest,
    ensure_bogota_datetime,
)
from app.repository import DataStore, JsonRepository
from app.rules import calculate_cancellation_amounts, validate_booking_creation, ensure_booking_can_be_cancelled


DEFAULT_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "seed.json"


def default_now() -> datetime:
    return datetime.now(BOGOTA_TZ)


def create_app(
    *,
    data_path: Path = DEFAULT_DATA_PATH,
    now_provider: Callable[[], datetime] = default_now,
) -> FastAPI:
    app = FastAPI(title="Booking Service", version="1.0.0")
    repository = JsonRepository(data_path)

    @app.exception_handler(DomainError)
    async def domain_error_handler(_, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error_code": exc.error_code, "message": exc.message},
        )

    @app.get("/api/v1/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/v1/bookings", response_model=BookingResponse, status_code=201)
    def create_booking(request: CreateBookingRequest) -> Booking:
        now = ensure_bogota_datetime(now_provider())

        def mutation(store: DataStore) -> Booking:
            user = store.users.get(request.user_id)
            if user is None:
                raise DomainError(ErrorCodes.USER_NOT_FOUND, "Usuario no encontrado.", status_code=404)

            service = store.services.get(request.service_id)
            if service is None:
                raise DomainError(ErrorCodes.SERVICE_NOT_FOUND, "Servicio no encontrado.", status_code=404)

            end_at = validate_booking_creation(
                user=user,
                service=service,
                start_at=request.start_at,
                bookings=list(store.bookings.values()),
                services_by_id=store.services,
                now=now,
            )

            booking = Booking(
                id=f"b-{uuid4()}",
                user_id=user.id,
                service_id=service.id,
                start_at=request.start_at,
                end_at=end_at,
                status=BookingStatus.ACTIVE,
                created_at=now,
            )
            store.bookings[booking.id] = booking
            return booking

        return repository.mutate(mutation)

    @app.delete("/api/v1/bookings/{booking_id}", response_model=CancellationResponse)
    def cancel_booking(booking_id: str) -> CancellationResponse:
        now = ensure_bogota_datetime(now_provider())

        def mutation(store: DataStore) -> CancellationResponse:
            booking = store.bookings.get(booking_id)
            if booking is None:
                raise DomainError(ErrorCodes.BOOKING_NOT_FOUND, "Reserva no encontrada.", status_code=404)

            ensure_booking_can_be_cancelled(booking)

            user = store.users.get(booking.user_id)
            if user is None:
                raise DomainError(ErrorCodes.USER_NOT_FOUND, "Usuario no encontrado.", status_code=404)

            service = store.services.get(booking.service_id)
            if service is None:
                raise DomainError(ErrorCodes.SERVICE_NOT_FOUND, "Servicio no encontrado.", status_code=404)

            refund_percentage, refund_amount_cents, charged_amount_cents = calculate_cancellation_amounts(
                user=user,
                service=service,
                booking=booking,
                now=now,
            )

            booking.status = BookingStatus.CANCELLED
            booking.cancelled_at = now
            booking.refund_percentage = refund_percentage
            booking.refund_amount_cents = refund_amount_cents
            booking.charged_amount_cents = charged_amount_cents
            store.bookings[booking.id] = booking

            return CancellationResponse(
                id=booking.id,
                status=booking.status,
                refund_percentage=refund_percentage,
                refund_amount_cents=refund_amount_cents,
                charged_amount_cents=charged_amount_cents,
                cancelled_at=now,
            )

        return repository.mutate(mutation)

    @app.get("/api/v1/users/{user_id}/bookings", response_model=list[BookingResponse])
    def list_user_bookings(
        user_id: str,
        from_at: Annotated[datetime, Query(alias="from")],
        to_at: Annotated[datetime, Query(alias="to")],
    ) -> list[Booking]:
        from_at = ensure_bogota_datetime(from_at)
        to_at = ensure_bogota_datetime(to_at)
        if from_at > to_at:
            raise DomainError(ErrorCodes.INVALID_DATE_RANGE, "El rango de fechas es inválido.")

        store = repository.read()
        if user_id not in store.users:
            raise DomainError(ErrorCodes.USER_NOT_FOUND, "Usuario no encontrado.", status_code=404)

        return [
            booking
            for booking in store.bookings.values()
            if booking.user_id == user_id and from_at <= booking.start_at <= to_at
        ]

    return app


app = create_app()

