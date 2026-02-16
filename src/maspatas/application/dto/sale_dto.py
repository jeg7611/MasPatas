from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SaleLineInputDTO:
    product_id: str
    quantity: int


@dataclass(frozen=True)
class RegisterSaleInputDTO:
    sale_id: str
    client_id: str
    lines: tuple[SaleLineInputDTO, ...]


@dataclass(frozen=True)
class RegisterSaleOutputDTO:
    sale_id: str
    total_amount: str
    currency: str
