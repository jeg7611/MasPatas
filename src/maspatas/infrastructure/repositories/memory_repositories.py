from __future__ import annotations

from decimal import Decimal

from maspatas.domain.entities.client import Client
from maspatas.domain.entities.inventory import InventoryAggregate
from maspatas.domain.entities.product import Product
from maspatas.domain.entities.sale import SaleAggregate
from maspatas.domain.ports.repositories import (
    ClientRepositoryPort,
    InventoryRepositoryPort,
    ProductRepositoryPort,
    SaleRepositoryPort,
)
from maspatas.domain.value_objects.common import ClientId, Money, ProductId


class InMemoryProductRepository(ProductRepositoryPort):
    def __init__(self, products: dict[str, Product] | None = None) -> None:
        self._products = products or {}

    @classmethod
    def with_seed(cls) -> "InMemoryProductRepository":
        return cls(
            products={
                "P-001": Product(id=ProductId("P-001"), name="Croquetas Premium", sku="CROQ-01", price=Money(Decimal("550.00"))),
                "P-002": Product(id=ProductId("P-002"), name="Correa Ajustable", sku="CORR-01", price=Money(Decimal("220.00"))),
            }
        )

    def get_by_id(self, product_id: ProductId) -> Product | None:
        return self._products.get(product_id.value)

    def save_product(self, product: Product) -> None:
        self._products[product.id.value] = product


class InMemoryClientRepository(ClientRepositoryPort):
    def __init__(self, clients: dict[str, Client] | None = None) -> None:
        self._clients = clients or {}

    @classmethod
    def with_seed(cls) -> "InMemoryClientRepository":
        return cls(clients={"C-001": Client(id=ClientId("C-001"), full_name="Ana Pérez", email="ana@cliente.com")})

    def get_by_id(self, client_id: ClientId) -> Client | None:
        return self._clients.get(client_id.value)

    def save_client(self, client: Client) -> None:
        self._clients[client.id.value] = client


class InMemoryInventoryRepository(InventoryRepositoryPort):
    def __init__(self, inventory: InventoryAggregate | None = None) -> None:
        self._inventory = inventory or InventoryAggregate()

    def get_inventory(self) -> InventoryAggregate:
        return self._inventory

    def save_inventory(self, inventory: InventoryAggregate) -> None:
        self._inventory = inventory


class InMemorySaleRepository(SaleRepositoryPort):
    def __init__(self) -> None:
        self.sales: list[SaleAggregate] = []

    def save_sale(self, sale: SaleAggregate) -> None:
        self.sales.append(sale)
