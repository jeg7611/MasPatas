from __future__ import annotations

from dataclasses import dataclass

from maspatas.domain.exceptions.domain_exceptions import BusinessRuleViolation
from maspatas.domain.value_objects.common import Money, ProductId


@dataclass(frozen=True)
class Product:
    id: ProductId
    name: str
    price: Money
    sku: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise BusinessRuleViolation("El nombre del producto es obligatorio")
        if not self.sku.strip():
            raise BusinessRuleViolation("El SKU es obligatorio")
