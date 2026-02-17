from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RegisterProductInputDTO:
    product_id: str
    name: str
    sku: str
    price_amount: str
    currency: str
    initial_stock: int = 0


@dataclass(frozen=True)
class RegisterProductOutputDTO:
    product_id: str
    name: str
    sku: str
    price_amount: str
    currency: str
    initial_stock: int
