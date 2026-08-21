"""In-process LRU + TTL cache for triage results.

Cache key: sha256(prompt_version + "\n" + user_text).
Cache value: TriageRes.model_dump() (a JSON-serializable dict).

The prompt version is part of the key on purpose — bumping PROMPT_VERSION in
service.py invalidates every cached entry automatically, which is what we want
when the system prompt changes.

Thread-safety: this cache is not safe for concurrent mutation across threads.
FastAPI's sync route handlers run on a single worker thread by default, so this
is fine for the project's deployment. If we ever switch to multi-worker or
async-handler setups, wrap get/put with a lock (or replace this with a
process-shared backend).
"""

import hashlib
import time
from collections import OrderedDict


class TriageCache:
    """LRU cache with optional TTL, keyed by sha256 digest."""

    def __init__(self, max_size: int, ttl_seconds: float | None):
        self.max_size = max_size
        self.ttl = ttl_seconds
        # OrderedDict preserves insertion order; we move_to_end on hit so the
        # oldest unused key sits at the front and is the one we evict.
        self._store: OrderedDict[str, tuple[dict, float | None]] = OrderedDict()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> dict | None:
        """Return the cached value for `key`, or None on miss/expired.

        Marks the key as most-recently-used on hit. Expired entries are evicted
        and treated as misses so the next put doesn't resurrect them.
        """
        if key not in self._store:
            self.misses += 1
            return None

        value, expires_at = self._store[key]

        if self.ttl is not None and expires_at is not None and time.monotonic() > expires_at:
            del self._store[key]
            self.misses += 1
            return None

        self._store.move_to_end(key)  # mark MRU
        self.hits += 1
        return value

    def put(self, key: str, value: dict) -> None:
        """Store `value` under `key`. If size exceeds max_size, evict LRU."""
        expires_at = time.monotonic() + self.ttl if self.ttl else None

        if key in self._store:
            self._store.move_to_end(key)

        self._store[key] = (value, expires_at)

        if len(self._store) > self.max_size:
            self._store.popitem(last=False)  # drop oldest

    def __len__(self) -> int:
        return len(self._store)


def make_key(prompt_version: str, user_text: str) -> str:
    """sha256(prompt_version + "\\n" + user_text) as a hex digest.

    The version delimiter (`"\\n"`) prevents collisions like
    `("v1", "abc")` vs `("v", "1abc")`. SHA-256 is stdlib and produces a
    fixed-length key we can log cleanly.
    """
    return hashlib.sha256(
        (prompt_version + "\n" + user_text).encode("utf-8")
    ).hexdigest()
