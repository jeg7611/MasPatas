from __future__ import annotations

from enum import Enum

from maspatas.domain.exceptions.domain_exceptions import UnauthorizedOperationError


class Role(str, Enum):
    ADMIN = "ADMIN"
    VENDEDOR = "VENDEDOR"
    INVENTARIO = "INVENTARIO"


class AuthorizationService:
    role_permissions: dict[Role, set[str]] = {
        Role.ADMIN: {"register_sale", "manage_inventory", "register_client"},
        Role.VENDEDOR: {"register_sale", "register_client"},
        Role.INVENTARIO: {"manage_inventory"},
    }

    def ensure_permission(self, role: Role, permission: str) -> None:
        permissions = self.role_permissions.get(role, set())
        if permission not in permissions:
            raise UnauthorizedOperationError(
                f"El rol {role.value} no tiene permiso para {permission}"
            )
