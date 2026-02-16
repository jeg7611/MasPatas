from __future__ import annotations

import structlog
from fastapi import Depends, FastAPI, HTTPException

from maspatas.application.dto.sale_dto import RegisterSaleInputDTO, SaleLineInputDTO
from maspatas.application.services.authorization import AuthorizationService, Role
from maspatas.application.use_cases.register_sale import RegisterSaleUseCase
from maspatas.domain.entities.inventory import InventoryAggregate, InventoryItem
from maspatas.domain.exceptions.domain_exceptions import DomainError
from maspatas.domain.value_objects.common import ProductId
from maspatas.infrastructure.logging.config import configure_logging
from maspatas.infrastructure.repositories.memory_repositories import (
    InMemoryClientRepository,
    InMemoryInventoryRepository,
    InMemoryProductRepository,
    InMemorySaleRepository,
)
from maspatas.infrastructure.resilience.concurrency import InMemoryLockAdapter
from maspatas.infrastructure.resilience.policy import ResiliencePolicy
from maspatas.infrastructure.security.auth import get_current_role
from maspatas.interfaces.api.schemas import RegisterSaleRequest, RegisterSaleResponse

configure_logging()
logger = structlog.get_logger(__name__)

app = FastAPI(title="MasPatas Inventory & Sales")

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
