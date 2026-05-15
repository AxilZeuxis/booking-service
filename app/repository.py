from __future__ import annotations

import json
import logging
import os
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, TypeVar

from pydantic import ValidationError

from app.models import BOGOTA_TZ, Booking, Service, User, ensure_bogota_datetime


logger = logging.getLogger(__name__)
T = TypeVar("T")


@dataclass
class DataStore:
    users: dict[str, User]
    services: dict[str, Service]
    bookings: dict[str, Booking]


class JsonRepository:
    def __init__(self, data_path: Path) -> None:
        self.data_path = data_path
        self._lock = threading.Lock()

    def read(self) -> DataStore:
        with self._lock:
            return self._load()

    def mutate(self, callback: Callable[[DataStore], T]) -> T:
        with self._lock:
            store = self._load()
            result = callback(store)
            self._save(store)
            return result

    def _load(self) -> DataStore:
        if not self.data_path.exists():
            return DataStore(users={}, services={}, bookings={})

        with self.data_path.open("r", encoding="utf-8") as file:
            raw_data = json.load(file)

        users = self._load_users(raw_data.get("users", []))
        services = self._load_services(raw_data.get("services", []))
        bookings = self._load_bookings(raw_data.get("bookings", []), services)

        return DataStore(users=users, services=services, bookings=bookings)

    def _save(self, store: DataStore) -> None:
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "users": [user.model_dump(mode="json") for user in store.users.values()],
            "services": [service.model_dump(mode="json") for service in store.services.values()],
            "bookings": [booking.model_dump(mode="json") for booking in store.bookings.values()],
        }

        temp_path = self.data_path.with_suffix(".tmp")
        with temp_path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2, ensure_ascii=False)
            file.write("\n")
        os.replace(temp_path, self.data_path)

    def _load_users(self, raw_users: list[dict[str, Any]]) -> dict[str, User]:
        users: dict[str, User] = {}
        for raw_user in raw_users:
            try:
                user = User.model_validate(raw_user)
            except ValidationError as exc:
                logger.warning("Skipping invalid user record: %s", exc)
                continue
            users[user.id] = user
        return users

    def _load_services(self, raw_services: list[dict[str, Any]]) -> dict[str, Service]:
        services: dict[str, Service] = {}
        for raw_service in raw_services:
            try:
                service = Service.model_validate(raw_service)
            except ValidationError as exc:
                logger.warning("Skipping invalid service record: %s", exc)
                continue
            services[service.id] = service
        return services

    def _load_bookings(
        self,
        raw_bookings: list[dict[str, Any]],
        services: dict[str, Service],
    ) -> dict[str, Booking]:
        bookings: dict[str, Booking] = {}
        for raw_booking in raw_bookings:
            normalized = dict(raw_booking)
            service_id = normalized.get("service_id")
            service = services.get(service_id)
            if service is None:
                logger.warning("Skipping booking with unknown service_id: %s", service_id)
                continue

            start_at = parse_seed_datetime(normalized.get("start_at"))
            if start_at is None:
                logger.warning("Skipping booking with invalid start_at: %s", normalized.get("id"))
                continue

            normalized["start_at"] = start_at
            normalized["end_at"] = parse_seed_datetime(normalized.get("end_at")) or (
                start_at + timedelta(minutes=service.duration_minutes)
            )

            created_at = parse_seed_datetime(normalized.get("created_at"))
            normalized["created_at"] = created_at or start_at

            if normalized.get("cancelled_at") is not None:
                normalized["cancelled_at"] = parse_seed_datetime(normalized.get("cancelled_at"))

            try:
                booking = Booking.model_validate(normalized)
            except ValidationError as exc:
                logger.warning("Skipping invalid booking record: %s", exc)
                continue
            bookings[booking.id] = booking
        return bookings


def parse_seed_datetime(value: Any) -> datetime | None:
    if value is None:
        return None

    if isinstance(value, datetime):
        return ensure_bogota_datetime(value)

    if not isinstance(value, str):
        return None

    normalized_value = value.strip()
    if not normalized_value:
        return None

    iso_value = normalized_value.replace("Z", "+00:00")
    try:
        return ensure_bogota_datetime(datetime.fromisoformat(iso_value))
    except ValueError:
        pass

    for date_format in ("%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M"):
        try:
            parsed = datetime.strptime(normalized_value, date_format)
            return parsed.replace(tzinfo=BOGOTA_TZ)
        except ValueError:
            continue

    return None

