"""In-process sliding-window rate limiter for LLM endpoints.

Single-process only: a multi-worker deployment must swap this for a shared store
(e.g. Redis). Keyed per workspace id.
"""
import time
from collections import defaultdict, deque

import config


class SlidingWindowLimiter:
    def __init__(self, max_calls: int, window_seconds: float):
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self._hits = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        q = self._hits[key]
        while q and q[0] <= now - self.window_seconds:
            q.popleft()
        if len(q) >= self.max_calls:
            return False
        q.append(now)
        return True

    def clear(self):
        self._hits.clear()


llm_limiter = SlidingWindowLimiter(config.LLM_RATE_LIMIT_PER_MINUTE, config.LLM_RATE_WINDOW_SECONDS)
