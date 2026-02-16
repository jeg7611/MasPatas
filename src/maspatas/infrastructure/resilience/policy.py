from __future__ import annotations

import signal
from contextlib import contextmanager
from typing import Callable, TypeVar

import pybreaker
from tenacity import retry, stop_after_attempt, wait_exponential

T = TypeVar("T")


class TimeoutError(Exception):
    pass


class ResiliencePolicy:
    def __init__(self) -> None:
        self._breaker = pybreaker.CircuitBreaker(fail_max=3, reset_timeout=30)

    @contextmanager
    def timeout(self, seconds: int):
        def _handler(signum, frame):  # type: ignore[no-untyped-def]
            raise TimeoutError(f"Tiempo máximo excedido: {seconds}s")

        old_handler = signal.signal(signal.SIGALRM, _handler)
        signal.alarm(seconds)
        try:
            yield
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=4), reraise=True)
    def with_retry(self, fn: Callable[[], T]) -> T:
        return fn()

    def protected_call(self, fn: Callable[[], T], timeout_seconds: int = 5) -> T:
        with self.timeout(timeout_seconds):
            return self._breaker.call(lambda: self.with_retry(fn))
