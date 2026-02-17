from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pymongo.database import Database

from maspatas.domain.entities.client import Client
from maspatas.domain.entities.inventory import InventoryAggregate, InventoryItem
from maspatas.domain.entities.product import Product
from maspatas.domain.entities.sale import SaleAggregate
from maspatas.domain.ports.repositories import (
    ClientRepositoryPort,
    InventoryRepositoryPort,
    ProductRepositoryPort,
    SaleRepositoryPort,
)
from maspatas.domain.value_objects.common import ClientId, Money, ProductId


class MongoProductRepository(ProductRepositoryPort):
    def __init__(self, db: Database) -> None:
        self._db = db

    def get_by_id(self, product_id: ProductId) -> Product | None:
        doc = self._db.products.find_one({"_id": product_id.value})
        if not doc:
            return None
        return Product(
            id=ProductId(doc["id"]),
            name=doc["name"],
            sku=doc["sku"],
            price=Money(amount=Decimal(doc["price_amount"]), currency=doc["price_currency"]),
        )


class MongoClientRepository(ClientRepositoryPort):
    def __init__(self, db: Database) -> None:
        self._db = db

    def get_by_id(self, client_id: ClientId) -> Client | None:
        doc = self._db.clients.find_one({"_id": client_id.value})
        if not doc:
            return None
        return Client(id=ClientId(doc["id"]), full_name=doc["full_name"], email=doc["email"])


class MongoInventoryRepository(InventoryRepositoryPort):
    def __init__(self, db: Database) -> None:
        self._db = db

    def get_inventory(self) -> InventoryAggregate:
        docs = self._db.inventory.find({})
        items = {
            ProductId(doc["product_id"]): InventoryItem(product_id=ProductId(doc["product_id"]), stock=doc["stock"])
            for doc in docs
        }
        return InventoryAggregate(items=items)

    def save_inventory(self, inventory: InventoryAggregate) -> None:
        for item in inventory.items.values():
            self._db.inventory.update_one(
                {"_id": item.product_id.value},
                {"$set": {"product_id": item.product_id.value, "stock": item.stock}},
                upsert=True,
            )


class MongoSaleRepository(SaleRepositoryPort):
    def __init__(self, db: Database) -> None:
        self._db = db

    def save_sale(self, sale: SaleAggregate) -> None:
        self._db.sales.insert_one(
            {
                "_id": sale.sale_id,
                "sale_id": sale.sale_id,
                "client_id": sale.client_id.value,
                "created_at": sale.created_at.isoformat(),
                "total_amount": str(sale.total.amount),
                "currency": sale.total.currency,
                "lines": [
                    {
                        "product_id": line.product_id.value,
                        "quantity": line.quantity,
                        "unit_price_amount": str(line.unit_price.amount),
                        "currency": line.unit_price.currency,
                    }
                    for line in sale.lines
                ],
            }
        )


def parse_sale_datetime(raw_value: str) -> datetime:
    return datetime.fromisoformat(raw_value)
