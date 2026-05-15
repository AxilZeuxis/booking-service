from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import base_seed, write_seed


def test_create_booking_success(client: TestClient) -> None:
    response = client.post(
        "/api/v1/bookings",
        json={
            "user_id": "u-001",
            "service_id": "s-003",
            "start_at": "2026-05-19T10:00:00-05:00",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["user_id"] == "u-001"
    assert body["service_id"] == "s-003"
    assert body["status"] == "active"
    assert body["end_at"] == "2026-05-19T10:30:00-05:00"


def test_dashboard_is_served(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "Panel de reservas" in response.text


def test_catalog_endpoints_return_users_and_services(client: TestClient) -> None:
    users_response = client.get("/api/v1/users")
    services_response = client.get("/api/v1/services")

    assert users_response.status_code == 200
    assert services_response.status_code == 200
    assert users_response.json()[0]["id"] == "u-001"
    assert services_response.json()[0]["price_cents"] == 12000000


def test_create_booking_on_holiday_returns_422(client: TestClient) -> None:
    response = client.post(
        "/api/v1/bookings",
        json={
            "user_id": "u-001",
            "service_id": "s-003",
            "start_at": "2026-05-18T10:00:00-05:00",
        },
    )

    assert response.status_code == 422
    assert response.json()["error_code"] == "HOLIDAY_NOT_ALLOWED"


def test_create_booking_outside_business_hours_returns_422(client: TestClient) -> None:
    response = client.post(
        "/api/v1/bookings",
        json={
            "user_id": "u-001",
            "service_id": "s-001",
            "start_at": "2026-05-19T18:30:00-05:00",
        },
    )

    assert response.status_code == 422
    assert response.json()["error_code"] == "OUTSIDE_BUSINESS_HOURS"


def test_create_booking_insufficient_advance_returns_422(client: TestClient) -> None:
    response = client.post(
        "/api/v1/bookings",
        json={
            "user_id": "u-001",
            "service_id": "s-003",
            "start_at": "2026-05-15T09:00:00-05:00",
        },
    )

    assert response.status_code == 422
    assert response.json()["error_code"] == "INSUFFICIENT_ADVANCE"


def test_create_booking_professional_overlap_returns_422(seed_path) -> None:
    write_seed(
        seed_path,
        base_seed(
            [
                {
                    "id": "b-001",
                    "user_id": "u-002",
                    "service_id": "s-001",
                    "start_at": "2026-05-19T10:00:00-05:00",
                    "end_at": "2026-05-19T11:00:00-05:00",
                    "status": "active",
                    "created_at": "2026-05-15T08:00:00-05:00",
                }
            ]
        ),
    )
    from app.main import create_app
    from tests.conftest import FIXED_NOW

    client = TestClient(create_app(data_path=seed_path, now_provider=lambda: FIXED_NOW))

    response = client.post(
        "/api/v1/bookings",
        json={
            "user_id": "u-001",
            "service_id": "s-002",
            "start_at": "2026-05-19T10:30:00-05:00",
        },
    )

    assert response.status_code == 422
    assert response.json()["error_code"] == "PROFESSIONAL_OVERLAP"


def test_create_booking_user_limit_returns_422(seed_path) -> None:
    bookings = [
        {
            "id": f"b-00{index}",
            "user_id": "u-001",
            "service_id": "s-003",
            "start_at": start_at,
            "status": "active",
            "created_at": "2026-05-15T08:00:00-05:00",
        }
        for index, start_at in enumerate(
            [
                "2026-05-19T08:00:00-05:00",
                "2026-05-20T08:00:00-05:00",
                "2026-05-21T08:00:00-05:00",
            ],
            start=1,
        )
    ]
    write_seed(seed_path, base_seed(bookings))
    from app.main import create_app
    from tests.conftest import FIXED_NOW

    client = TestClient(create_app(data_path=seed_path, now_provider=lambda: FIXED_NOW))

    response = client.post(
        "/api/v1/bookings",
        json={
            "user_id": "u-001",
            "service_id": "s-003",
            "start_at": "2026-05-22T08:00:00-05:00",
        },
    )

    assert response.status_code == 422
    assert response.json()["error_code"] == "USER_BOOKING_LIMIT"


def test_cancel_booking_returns_amounts(seed_path) -> None:
    write_seed(
        seed_path,
        base_seed(
            [
                {
                    "id": "b-001",
                    "user_id": "u-001",
                    "service_id": "s-001",
                    "start_at": "2026-05-16T08:00:00-05:00",
                    "status": "active",
                    "created_at": "2026-05-15T08:00:00-05:00",
                }
            ]
        ),
    )
    from app.main import create_app
    from tests.conftest import FIXED_NOW

    client = TestClient(create_app(data_path=seed_path, now_provider=lambda: FIXED_NOW))

    response = client.delete("/api/v1/bookings/b-001")

    assert response.status_code == 200
    assert response.json()["refund_percentage"] == 50
    assert response.json()["refund_amount_cents"] == 6000000
    assert response.json()["charged_amount_cents"] == 6000000


def test_list_bookings_in_date_range(seed_path) -> None:
    write_seed(
        seed_path,
        base_seed(
            [
                {
                    "id": "b-001",
                    "user_id": "u-001",
                    "service_id": "s-001",
                    "start_at": "2026-05-19T10:00:00-05:00",
                    "status": "active",
                    "created_at": "2026-05-15T08:00:00-05:00",
                },
                {
                    "id": "b-002",
                    "user_id": "u-001",
                    "service_id": "s-003",
                    "start_at": "2026-05-25T10:00:00-05:00",
                    "status": "active",
                    "created_at": "2026-05-15T08:00:00-05:00",
                },
            ]
        ),
    )
    from app.main import create_app
    from tests.conftest import FIXED_NOW

    client = TestClient(create_app(data_path=seed_path, now_provider=lambda: FIXED_NOW))

    response = client.get(
        "/api/v1/users/u-001/bookings",
        params={
            "from": "2026-05-19T00:00:00-05:00",
            "to": "2026-05-20T23:59:59-05:00",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == "b-001"
