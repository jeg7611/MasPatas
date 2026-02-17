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


class ProductResponse(BaseModel):
    id: str
    name: str
    sku: str
    price_amount: str
    currency: str


class ClientResponse(BaseModel):
    id: str
    full_name: str
    email: str


class InventoryItemResponse(BaseModel):
    product_id: str
    stock: int


class SaleLineResponse(BaseModel):
    product_id: str
    quantity: int
    unit_price: str
    subtotal: str


class SaleResponse(BaseModel):
    sale_id: str
    client_id: str
    created_at: str
    total_amount: str
    currency: str
    lines: list[SaleLineResponse]
