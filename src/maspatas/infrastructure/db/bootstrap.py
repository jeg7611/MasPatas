from __future__ import annotations

import os

import psycopg2
from sqlalchemy.orm import Session

from maspatas.domain.value_objects.common import ProductId
from maspatas.infrastructure.db.models import ClientModel, InventoryModel, ProductModel
from maspatas.infrastructure.repositories.memory_repositories import InMemoryClientRepository, InMemoryProductRepository


def _build_admin_dsn() -> str:
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    user = os.getenv("POSTGRES_USER", "maspatas")
    password = os.getenv("POSTGRES_PASSWORD", "maspatas")
    dbname = os.getenv("POSTGRES_ADMIN_DB", "postgres")
    return f"dbname={dbname} user={user} password={password} host={host} port={port}"


def create_database_if_not_exists() -> None:
    database_name = os.getenv("POSTGRES_DB", "maspatas")
    connection = psycopg2.connect(_build_admin_dsn())
    connection.autocommit = True
    cursor = connection.cursor()
    cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database_name,))
    exists = cursor.fetchone()
    if not exists:
        cursor.execute(f'CREATE DATABASE "{database_name}"')
    cursor.close()
    connection.close()


def seed_if_empty(session: Session) -> None:
    has_products = session.query(ProductModel).first() is not None
    if has_products:
        return

    products = InMemoryProductRepository.with_seed()._products  # noqa: SLF001
    clients = InMemoryClientRepository.with_seed()._clients  # noqa: SLF001

    for product in products.values():
        session.add(
            ProductModel(
                id=product.id.value,
                name=product.name,
                sku=product.sku,
                price_amount=product.price.amount,
                price_currency=product.price.currency,
            )
        )

    for client in clients.values():
        session.add(ClientModel(id=client.id.value, full_name=client.full_name, email=client.email))

    session.add_all(
        [
            InventoryModel(product_id=ProductId("P-001").value, stock=15),
            InventoryModel(product_id=ProductId("P-002").value, stock=8),
        ]
    )
    session.commit()
