from __future__ import annotations

from maspatas.application.dto.sale_dto import RegisterSaleInputDTO, SaleLineInputDTO
from maspatas.application.services.authorization import AuthorizationService, Role
from maspatas.application.use_cases.register_sale import RegisterSaleUseCase
from maspatas.domain.entities.inventory import InventoryAggregate, InventoryItem
from maspatas.domain.exceptions.domain_exceptions import BusinessRuleViolation, UnauthorizedOperationError
from maspatas.domain.value_objects.common import ProductId
from maspatas.infrastructure.repositories.memory_repositories import (
    InMemoryClientRepository,
    InMemoryInventoryRepository,
    InMemoryProductRepository,
    InMemorySaleRepository,
)
from maspatas.infrastructure.resilience.concurrency import InMemoryLockAdapter


def _build_use_case(initial_stock: int = 10) -> RegisterSaleUseCase:
    inventory_repo = InMemoryInventoryRepository(
        InventoryAggregate(items={ProductId("P-001"): InventoryItem(product_id=ProductId("P-001"), stock=initial_stock)})
    )
    return RegisterSaleUseCase(
        product_repo=InMemoryProductRepository.with_seed(),
        client_repo=InMemoryClientRepository.with_seed(),
        inventory_repo=inventory_repo,
        sale_repo=InMemorySaleRepository(),
        concurrency=InMemoryLockAdapter(),
        authz=AuthorizationService(),
    )


def test_register_sale_successfully() -> None:
    use_case = _build_use_case(initial_stock=10)

    output = use_case.execute(
        RegisterSaleInputDTO(
            sale_id="S-001",
            client_id="C-001",
            lines=(SaleLineInputDTO(product_id="P-001", quantity=2),),
        ),
        role=Role.VENDEDOR,
    )

    assert output.sale_id == "S-001"
    assert output.currency == "MXN"


def test_register_sale_fails_when_stock_is_insufficient() -> None:
    use_case = _build_use_case(initial_stock=1)

    try:
        use_case.execute(
            RegisterSaleInputDTO(
                sale_id="S-002",
                client_id="C-001",
                lines=(SaleLineInputDTO(product_id="P-001", quantity=2),),
            ),
            role=Role.VENDEDOR,
        )
    except BusinessRuleViolation as exc:
        assert "Stock insuficiente" in str(exc)
    else:
        raise AssertionError("Se esperaba error por stock insuficiente")


def test_register_sale_fails_for_inventory_role() -> None:
    use_case = _build_use_case(initial_stock=10)

    try:
        use_case.execute(
            RegisterSaleInputDTO(
                sale_id="S-003",
                client_id="C-001",
                lines=(SaleLineInputDTO(product_id="P-001", quantity=1),),
            ),
            role=Role.INVENTARIO,
        )
    except UnauthorizedOperationError as exc:
        assert "no tiene permiso" in str(exc)
    else:
        raise AssertionError("Se esperaba error de autorización")
