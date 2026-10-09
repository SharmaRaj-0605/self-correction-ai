import hashlib
import json
import logging
import time
from typing import Any

from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class Cache:
   

    def __init__(self, redis_url: str, ttl: int):
        self.redis = Redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        self.ttl = ttl
        self._memory: dict[str, tuple[float, str]] = {}

    @staticmethod
    def key(prompt: str) -> str:
        digest = hashlib.sha256(prompt.strip().lower().encode("utf-8")).hexdigest()
        return f"agent-result:{digest}"

    def _memory_get(self, key: str) -> str | None:
        item = self._memory.get(key)
        if not item:
            return None
        expires_at, raw = item
        if expires_at < time.time():
            self._memory.pop(key, None)
            return None
        return raw

    async def get(self, prompt: str) -> Any | None:
        key = self.key(prompt)
        try:
            raw = await self.redis.get(key)
        except Exception as exc:
            logger.warning("Redis get failed, using memory cache: %s", exc)
            raw = self._memory_get(key)
        return json.loads(raw) if raw else None

    async def set(self, prompt: str, value: Any) -> None:
        key = self.key(prompt)
        raw = json.dumps(value)
        try:
            await self.redis.setex(key, self.ttl, raw)
        except Exception as exc:
            logger.warning("Redis set failed, using memory cache: %s", exc)
            if len(self._memory) > 200:  # keep the fallback small
                self._memory.clear()
            self._memory[key] = (time.time() + self.ttl, raw)

    async def ping(self) -> bool:
        return bool(await self.redis.ping())
