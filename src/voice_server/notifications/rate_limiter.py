from __future__ import annotations

import time


class RateLimiter:
    """In-memory token bucket rate limiter. One token per key per window."""

    def __init__(self, window_seconds: int = 60) -> None:
        self._window = window_seconds
        self._last_sent: dict[str, float] = {}

    def allow(self, key: str) -> bool:
        now = time.time()
        last = self._last_sent.get(key, 0.0)
        if now - last >= self._window:
            self._last_sent[key] = now
            return True
        return False

    def reset(self, key: str) -> None:
        self._last_sent.pop(key, None)
