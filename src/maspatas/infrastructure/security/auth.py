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


def get_current_role(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Role:
    token = credentials.credentials
    role = _TOKEN_TO_ROLE.get(token)
    if not role:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    return role
