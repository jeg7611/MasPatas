from __future__ import annotations

from maspatas.application.dto.product_dto import RegisterProductInputDTO
from maspatas.application.services.authorization import AuthorizationService, Role
from maspatas.application.use_cases.register_product import RegisterProductUseCase
from maspatas.domain.entities.inventory import InventoryAggregate
from maspatas.domain.exceptions.domain_exceptions import BusinessRuleViolation, UnauthorizedOperationError
from maspatas.domain.value_objects.common import ProductId
from maspatas.infrastructure.repositories.memory_repositories import InMemoryInventoryRepository, InMemoryProductRepository
from maspatas.infrastructure.resilience.concurrency import InMemoryLockAdapter


def _build_use_case() -> RegisterProductUseCase:
    return RegisterProductUseCase(
        product_repo=InMemoryProductRepository.with_seed(),
        inventory_repo=InMemoryInventoryRepository(InventoryAggregate()),
        concurrency=InMemoryLockAdapter(),
        authz=AuthorizationService(),
    )


def test_register_product_successfully() -> None:
    use_case = _build_use_case()

    output = use_case.execute(
        RegisterProductInputDTO(
            product_id="P-900",
            name="Premio de entrenamiento",
            sku="PRE-900",
            price_amount="45.00",
            currency="MXN",
            initial_stock=10,
        ),
        role=Role.INVENTARIO,
    )

    assert output.product_id == "P-900"
    assert output.initial_stock == 10


def test_register_product_fails_when_id_exists() -> None:
    use_case = _build_use_case()

    try:
        use_case.execute(
            RegisterProductInputDTO(
                product_id="P-001",
                name="Duplicado",
                sku="DUP-001",
                price_amount="10.00",
                currency="MXN",
                initial_stock=0,
            ),
            role=Role.ADMIN,
        )
    except BusinessRuleViolation as exc:
        assert "Ya existe un producto" in str(exc)
    else:
        raise AssertionError("Se esperaba producto duplicado")


def test_register_product_fails_for_seller_role() -> None:
    use_case = _build_use_case()

    try:
        use_case.execute(
            RegisterProductInputDTO(
                product_id="P-901",
                name="Collar",
                sku="COL-901",
                price_amount="79.00",
                currency="MXN",
                initial_stock=3,
            ),
            role=Role.VENDEDOR,
        )
    except UnauthorizedOperationError as exc:
        assert "no tiene permiso" in str(exc)
    else:
        raise AssertionError("Se esperaba error de autorización")


def test_register_product_fails_with_negative_stock() -> None:
    use_case = _build_use_case()

    try:
        use_case.execute(
            RegisterProductInputDTO(
                product_id="P-902",
                name="Transportadora",
                sku="TRA-902",
                price_amount="500.00",
                currency="MXN",
                initial_stock=-1,
            ),
            role=Role.ADMIN,
        )
    except BusinessRuleViolation as exc:
        assert "stock inicial negativo" in str(exc)
    else:
        raise AssertionError("Se esperaba error por stock inicial negativo")


def test_register_product_updates_inventory() -> None:
    inventory_repo = InMemoryInventoryRepository(InventoryAggregate())
    use_case = RegisterProductUseCase(
        product_repo=InMemoryProductRepository.with_seed(),
        inventory_repo=inventory_repo,
        concurrency=InMemoryLockAdapter(),
        authz=AuthorizationService(),
    )

    use_case.execute(
        RegisterProductInputDTO(
            product_id="P-903",
            name="Peine",
            sku="PEI-903",
            price_amount="20.00",
            currency="MXN",
            initial_stock=7,
        ),
        role=Role.ADMIN,
    )

    inventory = inventory_repo.get_inventory()
    assert inventory.get_item(ProductId("P-903")).stock == 7
