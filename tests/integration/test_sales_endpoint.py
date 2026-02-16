from __future__ import annotations

from fastapi.testclient import TestClient

from maspatas.interfaces.api.main import app


client = TestClient(app)


def test_register_sale_endpoint_ok() -> None:
    response = client.post(
        "/sales",
        headers={"Authorization": "Bearer seller-token"},
        json={
            "sale_id": "S-100",
            "client_id": "C-001",
            "lines": [{"product_id": "P-001", "quantity": 1}],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["sale_id"] == "S-100"


def test_register_sale_endpoint_unauthorized() -> None:
    response = client.post(
        "/sales",
        headers={"Authorization": "Bearer invalid"},
        json={
            "sale_id": "S-101",
            "client_id": "C-001",
            "lines": [{"product_id": "P-001", "quantity": 1}],
        },
    )

    assert response.status_code == 401
