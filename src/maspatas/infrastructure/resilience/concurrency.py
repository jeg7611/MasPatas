from __future__ import annotations

from contextlib import contextmanager
from threading import Lock

from maspatas.domain.ports.concurrency import ConcurrencyControlPort


class InMemoryLockAdapter(ConcurrencyControlPort):
    def __init__(self) -> None:
        self._locks: dict[str, Lock] = {}

    @contextmanager
    def lock(self, key: str):
        if key not in self._locks:
            self._locks[key] = Lock()
        lock = self._locks[key]
        lock.acquire()
        try:
            yield
        finally:
            lock.release()
