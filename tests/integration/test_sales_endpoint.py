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


def test_catalog_and_inventory_endpoints() -> None:
    products_response = client.get("/products")
    assert products_response.status_code == 200
    products = products_response.json()
    assert len(products) >= 1

    clients_response = client.get("/clients")
    assert clients_response.status_code == 200
    clients = clients_response.json()
    assert len(clients) >= 1

    inventory_response = client.get("/inventory")
    assert inventory_response.status_code == 200
    inventory = inventory_response.json()
    assert len(inventory) >= 1


def test_sales_query_endpoints_and_openapi_paths() -> None:
    sale_id = "S-102"
    client.post(
        "/sales",
        headers={"Authorization": "Bearer seller-token"},
        json={
            "sale_id": sale_id,
            "client_id": "C-001",
            "lines": [{"product_id": "P-001", "quantity": 1}],
        },
    )

    get_sale_response = client.get(f"/sales/{sale_id}")
    assert get_sale_response.status_code == 200
    assert get_sale_response.json()["sale_id"] == sale_id

    list_sales_response = client.get("/sales")
    assert list_sales_response.status_code == 200
    assert any(sale["sale_id"] == sale_id for sale in list_sales_response.json())

    openapi_response = client.get("/openapi.json")
    assert openapi_response.status_code == 200
    openapi_paths = openapi_response.json()["paths"]
    assert "/products" in openapi_paths
    assert "/clients" in openapi_paths
    assert "/inventory" in openapi_paths
    assert "/sales" in openapi_paths
