from __future__ import annotations

import os
from decimal import Decimal

import structlog
from fastapi import Depends, FastAPI, HTTPException

from maspatas.application.dto.sale_dto import RegisterSaleInputDTO, SaleLineInputDTO
from maspatas.application.services.authorization import AuthorizationService, Role
from maspatas.application.use_cases.register_sale import RegisterSaleUseCase
from maspatas.domain.entities.inventory import InventoryAggregate, InventoryItem
from maspatas.domain.exceptions.domain_exceptions import DomainError
from maspatas.domain.value_objects.common import ClientId, ProductId
from maspatas.infrastructure.db.bootstrap import create_database_if_not_exists, seed_if_empty
from maspatas.infrastructure.db.models import ClientModel, InventoryModel, ProductModel, SaleLineModel, SaleModel
from maspatas.infrastructure.db.session import SessionLocal, init_db
from maspatas.infrastructure.logging.config import configure_logging
from maspatas.infrastructure.repositories.memory_repositories import (
    InMemoryClientRepository,
    InMemoryInventoryRepository,
    InMemoryProductRepository,
    InMemorySaleRepository,
)
from maspatas.infrastructure.repositories.sqlalchemy_repositories import (
    SQLAlchemyClientRepository,
    SQLAlchemyInventoryRepository,
    SQLAlchemyProductRepository,
    SQLAlchemySaleRepository,
)
from maspatas.infrastructure.resilience.concurrency import InMemoryLockAdapter
from maspatas.infrastructure.resilience.policy import ResiliencePolicy
from maspatas.infrastructure.security.auth import get_current_role
from maspatas.interfaces.api.schemas import RegisterSaleRequest, RegisterSaleResponse
from maspatas.interfaces.api.schemas import (
    ClientResponse,
    InventoryItemResponse,
    ProductResponse,
    SaleLineResponse,
    SaleResponse,
)

configure_logging()
logger = structlog.get_logger(__name__)

app = FastAPI(title="MasPatas Inventory & Sales")

backend = os.getenv("MASPATAS_REPOSITORY_BACKEND", "memory").lower()

if backend == "postgres":
    create_database_if_not_exists()
    init_db()
    db_session = SessionLocal()
    seed_if_empty(db_session)

    product_repo = SQLAlchemyProductRepository(session=db_session)
    client_repo = SQLAlchemyClientRepository(session=db_session)
    inventory_repo = SQLAlchemyInventoryRepository(session=db_session)
    sale_repo = SQLAlchemySaleRepository(session=db_session)
else:
    db_session = None
    product_repo = InMemoryProductRepository.with_seed()
    client_repo = InMemoryClientRepository.with_seed()
    inventory_repo = InMemoryInventoryRepository(
        InventoryAggregate(
            items={
                ProductId("P-001"): InventoryItem(product_id=ProductId("P-001"), stock=15),
                ProductId("P-002"): InventoryItem(product_id=ProductId("P-002"), stock=8),
            }
        )
    )
    sale_repo = InMemorySaleRepository()

concurrency = InMemoryLockAdapter()
authz = AuthorizationService()
resilience = ResiliencePolicy()

use_case = RegisterSaleUseCase(
    product_repo=product_repo,
    client_repo=client_repo,
    inventory_repo=inventory_repo,
    sale_repo=sale_repo,
    concurrency=concurrency,
    authz=authz,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/products", response_model=list[ProductResponse], tags=["Products"])
def list_products() -> list[ProductResponse]:
    if db_session is None:
        products = product_repo._products.values()  # noqa: SLF001
        return [
            ProductResponse(
                id=product.id.value,
                name=product.name,
                sku=product.sku,
                price_amount=str(product.price.amount),
                currency=product.price.currency,
            )
            for product in products
        ]

    models = db_session.query(ProductModel).all()
    return [
        ProductResponse(
            id=product.id,
            name=product.name,
            sku=product.sku,
            price_amount=str(Decimal(product.price_amount)),
            currency=product.price_currency,
        )
        for product in models
    ]


@app.get("/products/{product_id}", response_model=ProductResponse, tags=["Products"])
def get_product(product_id: str) -> ProductResponse:
    if db_session is None:
        product = product_repo.get_by_id(ProductId(product_id))
        if not product:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        return ProductResponse(
            id=product.id.value,
            name=product.name,
            sku=product.sku,
            price_amount=str(product.price.amount),
            currency=product.price.currency,
        )

    product = db_session.get(ProductModel, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return ProductResponse(
        id=product.id,
        name=product.name,
        sku=product.sku,
        price_amount=str(Decimal(product.price_amount)),
        currency=product.price_currency,
    )


@app.get("/clients", response_model=list[ClientResponse], tags=["Clients"])
def list_clients() -> list[ClientResponse]:
    if db_session is None:
        return [
            ClientResponse(id=client.id.value, full_name=client.full_name, email=client.email)
            for client in client_repo._clients.values()  # noqa: SLF001
        ]

    models = db_session.query(ClientModel).all()
    return [ClientResponse(id=client.id, full_name=client.full_name, email=client.email) for client in models]


@app.get("/clients/{client_id}", response_model=ClientResponse, tags=["Clients"])
def get_client(client_id: str) -> ClientResponse:
    if db_session is None:
        client = client_repo.get_by_id(client_id=ClientId(client_id))
        if not client:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        return ClientResponse(id=client.id.value, full_name=client.full_name, email=client.email)

    client = db_session.get(ClientModel, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return ClientResponse(id=client.id, full_name=client.full_name, email=client.email)


@app.get("/inventory", response_model=list[InventoryItemResponse], tags=["Inventory"])
def get_inventory() -> list[InventoryItemResponse]:
    inventory = inventory_repo.get_inventory()
    return [InventoryItemResponse(product_id=item.product_id.value, stock=item.stock) for item in inventory.items.values()]


@app.get("/sales", response_model=list[SaleResponse], tags=["Sales"])
def list_sales() -> list[SaleResponse]:
    if db_session is None:
        return [
            SaleResponse(
                sale_id=sale.sale_id,
                client_id=sale.client_id.value,
                created_at=sale.created_at.isoformat(),
                total_amount=str(sale.total.amount),
                currency=sale.total.currency,
                lines=[
                    SaleLineResponse(
                        product_id=line.product_id.value,
                        quantity=line.quantity,
                        unit_price=str(line.unit_price.amount),
                        subtotal=str(line.subtotal.amount),
                    )
                    for line in sale.lines
                ],
            )
            for sale in sale_repo.sales
        ]

    sales_models = db_session.query(SaleModel).all()
    response: list[SaleResponse] = []
    for sale in sales_models:
        line_models = db_session.query(SaleLineModel).filter(SaleLineModel.sale_id == sale.sale_id).all()
        response.append(
            SaleResponse(
                sale_id=sale.sale_id,
                client_id=sale.client_id,
                created_at=sale.created_at.isoformat(),
                total_amount=str(Decimal(sale.total_amount)),
                currency=sale.currency,
                lines=[
                    SaleLineResponse(
                        product_id=line.product_id,
                        quantity=line.quantity,
                        unit_price=str(Decimal(line.unit_price_amount)),
                        subtotal=str(Decimal(line.unit_price_amount) * line.quantity),
                    )
                    for line in line_models
                ],
            )
        )
    return response


@app.get("/sales/{sale_id}", response_model=SaleResponse, tags=["Sales"])
def get_sale(sale_id: str) -> SaleResponse:
    if db_session is None:
        sale = next((record for record in sale_repo.sales if record.sale_id == sale_id), None)
        if not sale:
            raise HTTPException(status_code=404, detail="Venta no encontrada")
        return SaleResponse(
            sale_id=sale.sale_id,
            client_id=sale.client_id.value,
            created_at=sale.created_at.isoformat(),
            total_amount=str(sale.total.amount),
            currency=sale.total.currency,
            lines=[
                SaleLineResponse(
                    product_id=line.product_id.value,
                    quantity=line.quantity,
                    unit_price=str(line.unit_price.amount),
                    subtotal=str(line.subtotal.amount),
                )
                for line in sale.lines
            ],
        )

    sale = db_session.get(SaleModel, sale_id)
    if not sale:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    line_models = db_session.query(SaleLineModel).filter(SaleLineModel.sale_id == sale_id).all()
    return SaleResponse(
        sale_id=sale.sale_id,
        client_id=sale.client_id,
        created_at=sale.created_at.isoformat(),
        total_amount=str(Decimal(sale.total_amount)),
        currency=sale.currency,
        lines=[
            SaleLineResponse(
                product_id=line.product_id,
                quantity=line.quantity,
                unit_price=str(Decimal(line.unit_price_amount)),
                subtotal=str(Decimal(line.unit_price_amount) * line.quantity),
            )
            for line in line_models
        ],
    )


@app.post("/sales", response_model=RegisterSaleResponse)
def register_sale(
    request: RegisterSaleRequest,
    role: Role = Depends(get_current_role),
) -> RegisterSaleResponse:
    try:
        dto = RegisterSaleInputDTO(
            sale_id=request.sale_id,
            client_id=request.client_id,
            lines=tuple(SaleLineInputDTO(product_id=line.product_id, quantity=line.quantity) for line in request.lines),
        )

        result = resilience.protected_call(lambda: use_case.execute(dto, role), timeout_seconds=5)
        logger.info("sale_registered", sale_id=result.sale_id, total=result.total_amount, currency=result.currency, role=role.value)
        return RegisterSaleResponse(**result.__dict__)
    except DomainError as exc:
        logger.warning("domain_error", detail=str(exc), role=role.value)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.error("unexpected_error", detail=str(exc))
        raise HTTPException(status_code=500, detail="Error interno") from exc
