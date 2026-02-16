from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from maspatas.domain.exceptions.domain_exceptions import BusinessRuleViolation
from maspatas.domain.value_objects.common import ClientId, Money, ProductId


@dataclass(frozen=True)
class SaleLine:
    product_id: ProductId
    quantity: int
    unit_price: Money

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise BusinessRuleViolation("La cantidad vendida debe ser mayor a 0")

    @property
    def subtotal(self) -> Money:
        return self.unit_price * self.quantity


@dataclass(frozen=True)
class SaleAggregate:
    sale_id: str
    client_id: ClientId
    lines: tuple[SaleLine, ...]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.lines:
            raise BusinessRuleViolation("Una venta debe contener al menos una línea")

    @property
    def total(self) -> Money:
        total = Money(amount=self.lines[0].subtotal.amount * 0, currency=self.lines[0].subtotal.currency)
        for line in self.lines:
            total = total + line.subtotal
        return total
