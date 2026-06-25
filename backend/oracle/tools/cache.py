"""On-disk response cache for the data API.

What: A tiny JSON file cache keyed by request signature, with a TTL.
Why: API-Football's free tier allows ~100 requests/day. Caching keeps us far under that,
makes runs reproducible, and lets demos work without spending quota live on camera.
How it fits: `api_football.py` wraps every network call in `cache.get_or_fetch(...)`.
On camera: "It only calls the API once per thing per day; after that it reads from this cache,
so a hundred reruns cost zero requests."
"""

from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ..config import CACHE_DIR


def _key(name: str, params: dict[str, Any]) -> str:
    raw = name + "?" + json.dumps(params, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()[:20]


class FileCache:
    """JSON file cache with per-entry TTL."""

    def __init__(self, directory: Path | None = None) -> None:
        self.dir = directory or CACHE_DIR
        self.dir.mkdir(parents=True, exist_ok=True)

    def path_for(self, name: str, params: dict[str, Any]) -> Path:
        # Endpoint names can contain "/" (e.g. "fixtures/headtohead"); flatten for a filename.
        safe = name.replace("/", "_")
        return self.dir / f"{safe}_{_key(name, params)}.json"

    def get(self, name: str, params: dict[str, Any], ttl_seconds: int) -> Any | None:
        path = self.path_for(name, params)
        if not path.exists():
            return None
        if ttl_seconds >= 0 and (time.time() - path.stat().st_mtime) > ttl_seconds:
            return None
        return json.loads(path.read_text())["value"]

    def set(self, name: str, params: dict[str, Any], value: Any) -> None:
        path = self.path_for(name, params)
        path.write_text(json.dumps({"name": name, "params": params, "value": value}, indent=2))

    def get_or_fetch(
        self,
        name: str,
        params: dict[str, Any],
        fetch: Callable[[], Any],
        ttl_seconds: int = 6 * 60 * 60,
    ) -> tuple[Any, bool]:
        """Return (value, from_cache). Fetches and stores on miss."""
        cached = self.get(name, params, ttl_seconds)
        if cached is not None:
            return cached, True
        value = fetch()
        self.set(name, params, value)
        return value, False
