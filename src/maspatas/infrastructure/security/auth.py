from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from maspatas.application.services.authorization import Role

security = HTTPBearer()

_TOKEN_TO_ROLE = {
    "admin-token": Role.ADMIN,
    "seller-token": Role.VENDEDOR,
    "inventory-token": Role.INVENTARIO,
}

_ROLE_TO_TOKEN = {
    Role.ADMIN: "admin-token",
    Role.VENDEDOR: "seller-token",
    Role.INVENTARIO: "inventory-token",
}

_USER_TO_ROLE = {
    "admin": Role.ADMIN,
    "seller": Role.VENDEDOR,
    "inventory": Role.INVENTARIO,
}


def get_current_role(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Role:
    token = credentials.credentials
    role = _TOKEN_TO_ROLE.get(token)
    if not role:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    return role


def issue_token(username: str, password: str) -> str | None:
    role = _USER_TO_ROLE.get(username.lower())
    if role is None or password != "maspatas123":
        return None
    return _ROLE_TO_TOKEN[role]
