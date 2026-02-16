from __future__ import annotations

from pydantic import BaseModel, Field


class SaleLineRequest(BaseModel):
    product_id: str = Field(min_length=1)
    quantity: int = Field(gt=0)


class RegisterSaleRequest(BaseModel):
    sale_id: str = Field(min_length=1)
    client_id: str = Field(min_length=1)
    lines: list[SaleLineRequest] = Field(min_length=1)


class RegisterSaleResponse(BaseModel):
    sale_id: str
    total_amount: str
    currency: str
