from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import AbstractContextManager


class ConcurrencyControlPort(ABC):
    @abstractmethod
    def lock(self, key: str) -> AbstractContextManager[None]:
        raise NotImplementedError
