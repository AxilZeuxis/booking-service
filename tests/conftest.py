from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


BOGOTA_TZ = ZoneInfo("America/Bogota")
FIXED_NOW = datetime(2026, 5, 15, 8, 0, tzinfo=BOGOTA_TZ)


def base_seed(bookings: list[dict] | None = None) -> dict:
    return {
        "users": [
            {"id": "u-001", "name": "Ana Pérez", "plan": "standard"},
            {"id": "u-002", "name": "Carlos Ruiz", "plan": "premium"},
        ],
        "services": [
            {
                "id": "s-001",
                "name": "Consulta general",
                "duration_minutes": 60,
                "professional_id": "p-001",
                "price_cents": 120000,
                "non_refundable": False,
            },
            {
                "id": "s-002",
                "name": "Taller especializado",
                "duration_minutes": 90,
                "professional_id": "p-001",
                "price_cents": 250000,
                "non_refundable": True,
            },
            {
                "id": "s-003",
                "name": "Sesión rápida",
                "duration_minutes": 30,
                "professional_id": "p-002",
                "price_cents": 80000,
                "non_refundable": False,
            },
        ],
        "bookings": bookings or [],
    }


def write_seed(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


@pytest.fixture
def seed_path(tmp_path: Path) -> Path:
    path = tmp_path / "seed.json"
    write_seed(path, base_seed())
    return path


@pytest.fixture
def client(seed_path: Path) -> TestClient:
    app = create_app(data_path=seed_path, now_provider=lambda: FIXED_NOW)
    return TestClient(app)

