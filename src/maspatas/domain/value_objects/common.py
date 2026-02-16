from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from maspatas.domain.exceptions.domain_exceptions import BusinessRuleViolation


@dataclass(frozen=True)
class ProductId:
    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise BusinessRuleViolation("ProductId no puede estar vacío")


@dataclass(frozen=True)
class ClientId:
    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise BusinessRuleViolation("ClientId no puede estar vacío")


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str = "MXN"

    def __post_init__(self) -> None:
        if self.amount < Decimal("0"):
            raise BusinessRuleViolation("El monto no puede ser negativo")
        if len(self.currency) != 3:
            raise BusinessRuleViolation("La moneda debe ser código ISO de 3 letras")

    def __add__(self, other: "Money") -> "Money":
        self._validate_same_currency(other)
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def __mul__(self, multiplier: int) -> "Money":
        return Money(amount=self.amount * Decimal(multiplier), currency=self.currency)

    def _validate_same_currency(self, other: "Money") -> None:
        if self.currency != other.currency:
            raise BusinessRuleViolation("No se pueden operar monedas diferentes")
