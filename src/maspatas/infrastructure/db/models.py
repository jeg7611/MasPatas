from __future__ import annotations

from sqlalchemy import Column, DateTime, Integer, Numeric, String
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class ProductModel(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    sku = Column(String, nullable=False, unique=True)
    price_amount = Column(Numeric(12, 2), nullable=False)
    price_currency = Column(String(3), nullable=False)


class ClientModel(Base):
    __tablename__ = "clients"

    id = Column(String, primary_key=True)
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False)


class InventoryModel(Base):
    __tablename__ = "inventory"

    product_id = Column(String, primary_key=True)
    stock = Column(Integer, nullable=False)


class SaleModel(Base):
    __tablename__ = "sales"

    sale_id = Column(String, primary_key=True)
    client_id = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False)
