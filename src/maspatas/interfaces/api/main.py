from __future__ import annotations

import os
from decimal import Decimal

import structlog
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.openapi.utils import get_openapi

from maspatas.application.dto.client_dto import RegisterClientInputDTO
from maspatas.application.dto.product_dto import RegisterProductInputDTO
from maspatas.application.dto.sale_dto import RegisterSaleInputDTO, SaleLineInputDTO
from maspatas.application.services.authorization import AuthorizationService, Role
from maspatas.application.use_cases.register_client import RegisterClientUseCase
from maspatas.application.use_cases.register_product import RegisterProductUseCase
from maspatas.application.use_cases.register_sale import RegisterSaleUseCase
from maspatas.domain.entities.inventory import InventoryAggregate, InventoryItem
from maspatas.domain.exceptions.domain_exceptions import DomainError
from maspatas.domain.value_objects.common import ClientId, ProductId
from maspatas.infrastructure.db.mongo import get_mongo_database, seed_if_empty
from maspatas.infrastructure.logging.config import configure_logging
from maspatas.infrastructure.repositories.memory_repositories import (
    InMemoryClientRepository,
    InMemoryInventoryRepository,
    InMemoryProductRepository,
    InMemorySaleRepository,
)
from maspatas.infrastructure.repositories.mongo_repositories import (
    MongoClientRepository,
    MongoInventoryRepository,
    MongoProductRepository,
    MongoSaleRepository,
    parse_sale_datetime,
)
from maspatas.infrastructure.resilience.concurrency import InMemoryLockAdapter
from maspatas.infrastructure.resilience.policy import ResiliencePolicy
from maspatas.infrastructure.security.auth import get_current_role, issue_token
from maspatas.interfaces.api.schemas import (
    RegisterClientRequest,
    RegisterClientResponse,
    RegisterProductRequest,
    RegisterProductResponse,
    RegisterSaleRequest,
    RegisterSaleResponse,
)
from maspatas.interfaces.api.schemas import (
    AuthTokenRequest,
    AuthTokenResponse,
    ClientResponse,
    InventoryItemResponse,
    ProductResponse,
    SaleLineResponse,
    SaleResponse,
)

configure_logging()
logger = structlog.get_logger(__name__)

app = FastAPI(title="MasPatas Inventory & Sales")


def custom_openapi() -> dict:
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version="1.0.0",
        description="API de inventario y ventas para MasPatas",
        routes=app.routes,
    )
    openapi_schema.setdefault("components", {}).setdefault("securitySchemes", {})["HTTPBearer"] = {
        "type": "http",
        "scheme": "bearer",
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

backend = os.getenv("MASPATAS_REPOSITORY_BACKEND", "mongo").lower()

if backend == "mongo":
    mongo_db = get_mongo_database()
    seed_if_empty(mongo_db)

    product_repo = MongoProductRepository(db=mongo_db)
    client_repo = MongoClientRepository(db=mongo_db)
    inventory_repo = MongoInventoryRepository(db=mongo_db)
    sale_repo = MongoSaleRepository(db=mongo_db)
else:
    mongo_db = None
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

register_sale_use_case = RegisterSaleUseCase(
    product_repo=product_repo,
    client_repo=client_repo,
    inventory_repo=inventory_repo,
    sale_repo=sale_repo,
    concurrency=concurrency,
    authz=authz,
)

register_product_use_case = RegisterProductUseCase(
    product_repo=product_repo,
    inventory_repo=inventory_repo,
    concurrency=concurrency,
    authz=authz,
)

register_client_use_case = RegisterClientUseCase(
    client_repo=client_repo,
    concurrency=concurrency,
    authz=authz,
)


@app.post("/auth/token", response_model=AuthTokenResponse, tags=["Auth"])
def generate_token(request: AuthTokenRequest) -> AuthTokenResponse:
    token = issue_token(username=request.username, password=request.password)
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
    return AuthTokenResponse(access_token=token, token_type="bearer")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/products", response_model=list[ProductResponse], tags=["Products"])
def list_products() -> list[ProductResponse]:
    if mongo_db is None:
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

    docs = mongo_db.products.find({})
    return [
        ProductResponse(
            id=product["id"],
            name=product["name"],
            sku=product["sku"],
            price_amount=str(Decimal(product["price_amount"])),
            currency=product["price_currency"],
        )
        for product in docs
    ]


@app.get("/products/{product_id}", response_model=ProductResponse, tags=["Products"])
def get_product(product_id: str) -> ProductResponse:
    if mongo_db is None:
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

    product = mongo_db.products.find_one({"_id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return ProductResponse(
        id=product["id"],
        name=product["name"],
        sku=product["sku"],
        price_amount=str(Decimal(product["price_amount"])),
        currency=product["price_currency"],
    )


@app.post("/products", response_model=RegisterProductResponse, tags=["Products"])
def register_product(
    request: RegisterProductRequest,
    role: Role = Depends(get_current_role),
) -> RegisterProductResponse:
    try:
        dto = RegisterProductInputDTO(
            product_id=request.product_id,
            name=request.name,
            sku=request.sku,
            price_amount=request.price_amount,
            currency=request.currency,
            initial_stock=request.initial_stock,
        )
        result = resilience.protected_call(lambda: register_product_use_case.execute(dto, role), timeout_seconds=5)
        logger.info("product_registered", product_id=result.product_id, role=role.value)
        return RegisterProductResponse(**result.__dict__)
    except DomainError as exc:
        logger.warning("domain_error", detail=str(exc), role=role.value)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.error("unexpected_error", detail=str(exc))
        raise HTTPException(status_code=500, detail="Error interno") from exc


@app.post("/clients", response_model=RegisterClientResponse, tags=["Clients"])
def register_client(
    request: RegisterClientRequest,
    role: Role = Depends(get_current_role),
) -> RegisterClientResponse:
    try:
        dto = RegisterClientInputDTO(
            client_id=request.client_id,
            full_name=request.full_name,
            email=request.email,
        )
        result = resilience.protected_call(lambda: register_client_use_case.execute(dto, role), timeout_seconds=5)
        logger.info("client_registered", client_id=result.client_id, role=role.value)
        return RegisterClientResponse(**result.__dict__)
    except DomainError as exc:
        logger.warning("domain_error", detail=str(exc), role=role.value)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.error("unexpected_error", detail=str(exc))
        raise HTTPException(status_code=500, detail="Error interno") from exc


@app.get("/clients", response_model=list[ClientResponse], tags=["Clients"])
def list_clients() -> list[ClientResponse]:
    if mongo_db is None:
        return [
            ClientResponse(id=client.id.value, full_name=client.full_name, email=client.email)
            for client in client_repo._clients.values()  # noqa: SLF001
        ]

    docs = mongo_db.clients.find({})
    return [ClientResponse(id=client["id"], full_name=client["full_name"], email=client["email"]) for client in docs]


@app.get("/clients/{client_id}", response_model=ClientResponse, tags=["Clients"])
def get_client(client_id: str) -> ClientResponse:
    if mongo_db is None:
        client = client_repo.get_by_id(client_id=ClientId(client_id))
        if not client:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        return ClientResponse(id=client.id.value, full_name=client.full_name, email=client.email)

    client = mongo_db.clients.find_one({"_id": client_id})
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return ClientResponse(id=client["id"], full_name=client["full_name"], email=client["email"])


@app.get("/inventory", response_model=list[InventoryItemResponse], tags=["Inventory"])
def get_inventory() -> list[InventoryItemResponse]:
    inventory = inventory_repo.get_inventory()
    return [InventoryItemResponse(product_id=item.product_id.value, stock=item.stock) for item in inventory.items.values()]


@app.get("/sales", response_model=list[SaleResponse], tags=["Sales"])
def list_sales() -> list[SaleResponse]:
    if mongo_db is None:
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

    sales_docs = mongo_db.sales.find({})
    return [
        SaleResponse(
            sale_id=sale["sale_id"],
            client_id=sale["client_id"],
            created_at=parse_sale_datetime(sale["created_at"]).isoformat(),
            total_amount=str(Decimal(sale["total_amount"])),
            currency=sale["currency"],
            lines=[
                SaleLineResponse(
                    product_id=line["product_id"],
                    quantity=line["quantity"],
                    unit_price=str(Decimal(line["unit_price_amount"])),
                    subtotal=str(Decimal(line["unit_price_amount"]) * line["quantity"]),
                )
                for line in sale["lines"]
            ],
        )
        for sale in sales_docs
    ]


@app.get("/sales/{sale_id}", response_model=SaleResponse, tags=["Sales"])
def get_sale(sale_id: str) -> SaleResponse:
    if mongo_db is None:
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

    sale = mongo_db.sales.find_one({"_id": sale_id})
    if not sale:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    return SaleResponse(
        sale_id=sale["sale_id"],
        client_id=sale["client_id"],
        created_at=parse_sale_datetime(sale["created_at"]).isoformat(),
        total_amount=str(Decimal(sale["total_amount"])),
        currency=sale["currency"],
        lines=[
            SaleLineResponse(
                product_id=line["product_id"],
                quantity=line["quantity"],
                unit_price=str(Decimal(line["unit_price_amount"])),
                subtotal=str(Decimal(line["unit_price_amount"]) * line["quantity"]),
            )
            for line in sale["lines"]
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

        result = resilience.protected_call(lambda: register_sale_use_case.execute(dto, role), timeout_seconds=5)
        logger.info("sale_registered", sale_id=result.sale_id, total=result.total_amount, currency=result.currency, role=role.value)
        return RegisterSaleResponse(**result.__dict__)
    except DomainError as exc:
        logger.warning("domain_error", detail=str(exc), role=role.value)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.error("unexpected_error", detail=str(exc))
        raise HTTPException(status_code=500, detail="Error interno") from exc
