from __future__ import annotations

from maspatas.application.dto.client_dto import RegisterClientInputDTO, RegisterClientOutputDTO
from maspatas.application.services.authorization import AuthorizationService, Role
from maspatas.domain.entities.client import Client
from maspatas.domain.exceptions.domain_exceptions import BusinessRuleViolation
from maspatas.domain.ports.concurrency import ConcurrencyControlPort
from maspatas.domain.ports.repositories import ClientRepositoryPort
from maspatas.domain.value_objects.common import ClientId


class RegisterClientUseCase:
    def __init__(
        self,
        client_repo: ClientRepositoryPort,
        concurrency: ConcurrencyControlPort,
        authz: AuthorizationService,
    ) -> None:
        self._client_repo = client_repo
        self._concurrency = concurrency
        self._authz = authz

    def execute(self, dto: RegisterClientInputDTO, role: Role) -> RegisterClientOutputDTO:
        self._authz.ensure_permission(role, "register_client")

        client_id = ClientId(dto.client_id)
        if self._client_repo.get_by_id(client_id) is not None:
            raise BusinessRuleViolation(f"Ya existe un cliente con id {dto.client_id}")

        lock_key = f"client:{dto.client_id}"
        with self._concurrency.lock(lock_key):
            client = Client(
                id=client_id,
                full_name=dto.full_name,
                email=dto.email,
            )
            self._client_repo.save_client(client)

            return RegisterClientOutputDTO(
                client_id=client.id.value,
                full_name=client.full_name,
                email=client.email,
            )
