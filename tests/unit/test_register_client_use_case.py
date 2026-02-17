from __future__ import annotations

from maspatas.application.dto.client_dto import RegisterClientInputDTO
from maspatas.application.services.authorization import AuthorizationService, Role
from maspatas.application.use_cases.register_client import RegisterClientUseCase
from maspatas.domain.exceptions.domain_exceptions import BusinessRuleViolation, UnauthorizedOperationError
from maspatas.infrastructure.repositories.memory_repositories import InMemoryClientRepository
from maspatas.infrastructure.resilience.concurrency import InMemoryLockAdapter


def _build_use_case() -> RegisterClientUseCase:
    return RegisterClientUseCase(
        client_repo=InMemoryClientRepository.with_seed(),
        concurrency=InMemoryLockAdapter(),
        authz=AuthorizationService(),
    )


def test_register_client_successfully() -> None:
    use_case = _build_use_case()

    output = use_case.execute(
        RegisterClientInputDTO(
            client_id="C-900",
            full_name="María López",
            email="maria@cliente.com",
        ),
        role=Role.VENDEDOR,
    )

    assert output.client_id == "C-900"
    assert output.email == "maria@cliente.com"


def test_register_client_fails_when_id_exists() -> None:
    use_case = _build_use_case()

    try:
        use_case.execute(
            RegisterClientInputDTO(
                client_id="C-001",
                full_name="Cliente Duplicado",
                email="duplicado@cliente.com",
            ),
            role=Role.ADMIN,
        )
    except BusinessRuleViolation as exc:
        assert "Ya existe un cliente" in str(exc)
    else:
        raise AssertionError("Se esperaba cliente duplicado")


def test_register_client_fails_for_inventory_role() -> None:
    use_case = _build_use_case()

    try:
        use_case.execute(
            RegisterClientInputDTO(
                client_id="C-901",
                full_name="Cliente Inventario",
                email="inventario@cliente.com",
            ),
            role=Role.INVENTARIO,
        )
    except UnauthorizedOperationError as exc:
        assert "no tiene permiso" in str(exc)
    else:
        raise AssertionError("Se esperaba error de autorización")
