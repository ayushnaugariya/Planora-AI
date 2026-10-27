"""Process-local, locked sliding-window quotas with bounded admission state."""

import math
import time
from collections import OrderedDict, deque
from collections.abc import Mapping
from threading import Lock


def positive_setting(env: Mapping[str, str], name: str, default: int, maximum: int) -> int:
    raw = env.get(name, str(default))
    if (
        not raw.isascii()
        or not raw.isdecimal()
        or len(raw) > len(str(maximum))
        or not 1 <= int(raw) <= maximum
    ):
        raise ValueError(f"{name} must be an integer between 1 and {maximum}")
    return int(raw)


def rate_settings(env: Mapping[str, str]) -> tuple[int, int, int]:
    limit = positive_setting(env, "RATE_LIMIT", 30, 10_000)
    window = positive_setting(env, "RATE_WINDOW", 60, 86_400)
    capacity = positive_setting(env, "RATE_MAX_CLIENTS", 10_000, 100_000)
    if limit * capacity > 1_000_000:
        raise ValueError("RATE_LIMIT * RATE_MAX_CLIENTS must not exceed 1000000")
    return limit, window, capacity


class SlidingWindowLimiter:
    def __init__(self) -> None:
        # Ordered by last admitted request, not last denied request. Idle queues
        # can therefore be expired from the front without a scan of active keys.
        self.hits: OrderedDict[str, deque[float]] = OrderedDict()
        self.lock = Lock()

    def check(self, ip: str, *, limit: int, window: int, capacity: int, now: float | None = None) -> int:
        """Return Retry-After seconds or 0. Explicit times must be monotonic."""
        with self.lock:
            # Read inside the lock so concurrent callers cannot reorder times.
            now = time.monotonic() if now is None else now
            cutoff = now - window
            while self.hits:
                first = next(iter(self.hits.values()))
                if first[-1] > cutoff:
                    break
                self.hits.popitem(last=False)
            queue = self.hits.get(ip)
            if queue is None:
                if len(self.hits) >= capacity:
                    # Never evict an active quota: cycling keys must not reset
                    # an existing limit. Deny admission until a whole slot frees.
                    first = next(iter(self.hits.values()))
                    return max(1, math.ceil(first[-1] + window - now))
                queue = deque()
                self.hits[ip] = queue
            while queue and queue[0] <= cutoff:
                queue.popleft()
            if len(queue) >= limit:
                return max(1, math.ceil(queue[0] + window - now))
            queue.append(now)
            self.hits.move_to_end(ip)
            return 0
