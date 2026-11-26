from typing import Any

from app.database.supabase_rest import SupabaseRestClient


class Repository:
    def __init__(self, db: SupabaseRestClient, user_id: str):
        self.db = db
        self.user_id = user_id

    async def list_owned(self, table: str, *, extra: dict[str, str] | None = None, order: str | None = None, limit: int = 100):
        query = {"user_id": f"eq.{self.user_id}"}
        query.update(extra or {})
        return await self.db.select(table, query=query, limit=limit, order=order)

    async def get_owned(self, table: str, record_id: str, *, id_column: str = "id"):
        rows = await self.db.select(table, query={id_column: f"eq.{record_id}", "user_id": f"eq.{self.user_id}"}, limit=1)
        return rows[0] if rows else None

    async def insert_owned(self, table: str, values: dict[str, Any]):
        payload = {**values, "user_id": self.user_id}
        rows = await self.db.insert(table, payload)
        return rows[0] if rows else payload

    async def update_owned(self, table: str, record_id: str, values: dict[str, Any]):
        rows = await self.db.update(table, values, query={"id": f"eq.{record_id}", "user_id": f"eq.{self.user_id}"})
        return rows[0] if rows else None
