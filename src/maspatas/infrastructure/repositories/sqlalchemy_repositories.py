from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

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
from maspatas.infrastructure.db.models import ClientModel, InventoryModel, ProductModel, SaleLineModel, SaleModel


class SQLAlchemyProductRepository(ProductRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, product_id: ProductId) -> Product | None:
        model = self._session.get(ProductModel, product_id.value)
        if not model:
            return None
        return Product(
            id=ProductId(model.id),
            name=model.name,
            sku=model.sku,
            price=Money(amount=Decimal(model.price_amount), currency=model.price_currency),
        )


class SQLAlchemyClientRepository(ClientRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, client_id: ClientId) -> Client | None:
        model = self._session.get(ClientModel, client_id.value)
        if not model:
            return None
        return Client(id=ClientId(model.id), full_name=model.full_name, email=model.email)

    def save_client(self, client: Client) -> None:
        self._session.add(ClientModel(id=client.id.value, full_name=client.full_name, email=client.email))
        self._session.commit()


class SQLAlchemyInventoryRepository(InventoryRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_inventory(self) -> InventoryAggregate:
        rows = self._session.query(InventoryModel).all()
        items = {
            ProductId(row.product_id): InventoryItem(product_id=ProductId(row.product_id), stock=row.stock)
            for row in rows
        }
        return InventoryAggregate(items=items)

    def save_inventory(self, inventory: InventoryAggregate) -> None:
        for item in inventory.items.values():
            row = self._session.get(InventoryModel, item.product_id.value)
            if row:
                row.stock = item.stock
            else:
                self._session.add(InventoryModel(product_id=item.product_id.value, stock=item.stock))
        self._session.commit()


class SQLAlchemySaleRepository(SaleRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def save_sale(self, sale: SaleAggregate) -> None:
        self._session.add(
            SaleModel(
                sale_id=sale.sale_id,
                client_id=sale.client_id.value,
                created_at=sale.created_at,
                total_amount=sale.total.amount,
                currency=sale.total.currency,
            )
        )
        self._session.flush()

        for line in sale.lines:
            self._session.add(
                SaleLineModel(
                    sale_id=sale.sale_id,
                    product_id=line.product_id.value,
                    quantity=line.quantity,
                    unit_price_amount=line.unit_price.amount,
                    currency=line.unit_price.currency,
                )
            )

        self._session.commit()
