"""
Rate limiter for LLM API calls.
Respects Claude API limit: 50 requests/minute (configurable).
Used by batch processor so we never exceed provider limits.
"""
import asyncio
import time
from collections import deque
from typing import Deque


class RateLimiter:
    """
    Sliding-window rate limiter: max N requests per minute.
    acquire() is async and waits until a slot is available.
    """

    def __init__(self, requests_per_minute: int = 50):
        self._rpm = max(1, requests_per_minute)
        self._window_seconds = 60.0
        self._timestamps: Deque[float] = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Wait until we can make one request without exceeding the limit."""
        while True:
            async with self._lock:
                now = time.monotonic()
                while self._timestamps and self._timestamps[0] < now - self._window_seconds:
                    self._timestamps.popleft()
                if len(self._timestamps) < self._rpm:
                    self._timestamps.append(time.monotonic())
                    return
                sleep_until = self._timestamps[0] + self._window_seconds - now
            if sleep_until > 0:
                await asyncio.sleep(sleep_until)
