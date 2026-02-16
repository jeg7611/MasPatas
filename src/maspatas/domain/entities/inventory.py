from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum

from maspatas.domain.exceptions.domain_exceptions import BusinessRuleViolation, InsufficientStockError
from maspatas.domain.value_objects.common import ProductId


class InventoryMovementType(str, Enum):
    ENTRADA = "ENTRADA"
    SALIDA = "SALIDA"
    AJUSTE = "AJUSTE"


@dataclass(frozen=True)
class InventoryItem:
    product_id: ProductId
    stock: int = 0

    def increase(self, quantity: int) -> "InventoryItem":
        if quantity <= 0:
            raise BusinessRuleViolation("La cantidad a ingresar debe ser positiva")
        return replace(self, stock=self.stock + quantity)

    def decrease(self, quantity: int) -> "InventoryItem":
        if quantity <= 0:
            raise BusinessRuleViolation("La cantidad a descontar debe ser positiva")
        if self.stock < quantity:
            raise InsufficientStockError(
                f"Stock insuficiente para {self.product_id.value}. Actual={self.stock}, requerido={quantity}"
            )
        return replace(self, stock=self.stock - quantity)

    def adjust(self, new_stock: int) -> "InventoryItem":
        if new_stock < 0:
            raise BusinessRuleViolation("No se permite stock negativo")
        return replace(self, stock=new_stock)


@dataclass(frozen=True)
class InventoryAggregate:
    items: dict[ProductId, InventoryItem] = field(default_factory=dict)

    def get_item(self, product_id: ProductId) -> InventoryItem:
        return self.items.get(product_id, InventoryItem(product_id=product_id, stock=0))

    def apply_movement(self, product_id: ProductId, movement_type: InventoryMovementType, quantity: int) -> "InventoryAggregate":
        current = self.get_item(product_id)
        if movement_type == InventoryMovementType.ENTRADA:
            updated = current.increase(quantity)
        elif movement_type == InventoryMovementType.SALIDA:
            updated = current.decrease(quantity)
        elif movement_type == InventoryMovementType.AJUSTE:
            updated = current.adjust(quantity)
        else:
            raise BusinessRuleViolation("Tipo de movimiento no soportado")

        new_items = dict(self.items)
        new_items[product_id] = updated
        return replace(self, items=new_items)
