from __future__ import annotations

import os
from decimal import Decimal

from pymongo import MongoClient
from pymongo.database import Database

from maspatas.infrastructure.repositories.memory_repositories import InMemoryClientRepository, InMemoryProductRepository


def get_mongo_database() -> Database:
    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGODB_DB", "maspatas")
    client = MongoClient(uri)
    return client[db_name]


def seed_if_empty(db: Database) -> None:
    if db.products.count_documents({}) > 0:
        return

    products = InMemoryProductRepository.with_seed()._products  # noqa: SLF001
    clients = InMemoryClientRepository.with_seed()._clients  # noqa: SLF001

    db.products.insert_many(
        [
            {
                "_id": product.id.value,
                "id": product.id.value,
                "name": product.name,
                "sku": product.sku,
                "price_amount": str(Decimal(product.price.amount)),
                "price_currency": product.price.currency,
            }
            for product in products.values()
        ]
    )

    db.clients.insert_many(
        [
            {
                "_id": client.id.value,
                "id": client.id.value,
                "full_name": client.full_name,
                "email": client.email,
            }
            for client in clients.values()
        ]
    )

    db.inventory.insert_many(
        [
            {"_id": "P-001", "product_id": "P-001", "stock": 15},
            {"_id": "P-002", "product_id": "P-002", "stock": 8},
        ]
    )
