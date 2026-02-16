from __future__ import annotations

from dataclasses import dataclass

from maspatas.domain.exceptions.domain_exceptions import BusinessRuleViolation
from maspatas.domain.value_objects.common import ClientId


@dataclass(frozen=True)
class Client:
    id: ClientId
    full_name: str
    email: str

    def __post_init__(self) -> None:
        if not self.full_name.strip():
            raise BusinessRuleViolation("El nombre del cliente es obligatorio")
        if "@" not in self.email:
            raise BusinessRuleViolation("Email del cliente inválido")
