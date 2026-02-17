from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RegisterClientInputDTO:
    client_id: str
    full_name: str
    email: str


@dataclass(frozen=True)
class RegisterClientOutputDTO:
    client_id: str
    full_name: str
    email: str
