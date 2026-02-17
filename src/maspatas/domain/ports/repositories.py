from __future__ import annotations

from abc import ABC, abstractmethod

from maspatas.domain.entities.client import Client
from maspatas.domain.entities.inventory import InventoryAggregate
from maspatas.domain.entities.product import Product
from maspatas.domain.entities.sale import SaleAggregate
from maspatas.domain.value_objects.common import ClientId, ProductId


class ProductRepositoryPort(ABC):
    @abstractmethod
    def get_by_id(self, product_id: ProductId) -> Product | None:
        raise NotImplementedError

    @abstractmethod
    def save_product(self, product: Product) -> None:
        raise NotImplementedError


class ClientRepositoryPort(ABC):
    @abstractmethod
    def get_by_id(self, client_id: ClientId) -> Client | None:
        raise NotImplementedError

    @abstractmethod
    def save_client(self, client: Client) -> None:
        raise NotImplementedError


class InventoryRepositoryPort(ABC):
    @abstractmethod
    def get_inventory(self) -> InventoryAggregate:
        raise NotImplementedError

    @abstractmethod
    def save_inventory(self, inventory: InventoryAggregate) -> None:
        raise NotImplementedError


class SaleRepositoryPort(ABC):
    @abstractmethod
    def save_sale(self, sale: SaleAggregate) -> None:
        raise NotImplementedError
