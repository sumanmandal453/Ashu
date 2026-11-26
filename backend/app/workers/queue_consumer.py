from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import asyncpg

from app.core.config import settings

logger = logging.getLogger(__name__)


class PGMQConsumer:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def read(self, queue_name: str) -> list[dict[str, Any]]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "select * from pgmq.read($1, $2, $3)",
                queue_name, settings.worker_visibility_timeout, settings.worker_batch_size,
            )
        messages = []
        for row in rows:
            item = dict(row)
            payload = item.get("message")
            if isinstance(payload, str):
                try:
                    item["message"] = json.loads(payload)
                except json.JSONDecodeError:
                    item["message"] = {}
            messages.append(item)
        return messages

    async def archive(self, queue_name: str, message_id: int) -> None:
        async with self.pool.acquire() as conn:
            await conn.fetchval("select pgmq.archive($1, $2)", queue_name, message_id)

    async def send(self, queue_name: str, message: dict[str, Any]) -> int:
        async with self.pool.acquire() as conn:
            return await conn.fetchval("select pgmq.send($1, $2::jsonb)", queue_name, json.dumps(message))
