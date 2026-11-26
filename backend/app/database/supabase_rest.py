from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx


class SupabaseRestClient:
    """Small request-scoped PostgREST/Storage client.

    For user requests, pass the Clerk session JWT as access_token and the Supabase
    publishable key as api_key. Never share a client configured with one user's JWT.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        access_token: str | None = None,
        clerk_token_from_request: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.access_token = access_token or clerk_token_from_request
        self._client = httpx.AsyncClient(timeout=timeout)

    def _headers(self, prefer: str | None = None) -> dict[str, str]:
        headers = {"apikey": self.api_key, "Accept": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        if prefer:
            headers["Prefer"] = prefer
        return headers

    async def select(
        self,
        table: str,
        *,
        query: dict[str, str] | None = None,
        select: str = "*",
        limit: int | None = None,
        order: str | None = None,
    ) -> list[dict[str, Any]]:
        params = {"select": select, **(query or {})}
        if limit is not None:
            params["limit"] = str(limit)
        if order:
            params["order"] = order
        response = await self._client.get(
            f"{self.base_url}/rest/v1/{quote(table, safe='')}",
            params=params,
            headers=self._headers(),
        )
        self._raise(response)
        return response.json()

    async def insert(self, table: str, rows: dict[str, Any] | list[dict[str, Any]], *, upsert: bool = False) -> list[dict[str, Any]]:
        headers = self._headers("resolution=merge-duplicates,return=representation" if upsert else "return=representation")
        if upsert:
            headers["Prefer"] += ",missing=default"
        response = await self._client.post(
            f"{self.base_url}/rest/v1/{quote(table, safe='')}",
            json=rows,
            headers=headers,
        )
        self._raise(response)
        return response.json() if response.content else []

    async def update(self, table: str, values: dict[str, Any], *, query: dict[str, str]) -> list[dict[str, Any]]:
        response = await self._client.patch(
            f"{self.base_url}/rest/v1/{quote(table, safe='')}",
            params=query,
            json=values,
            headers=self._headers("return=representation"),
        )
        self._raise(response)
        return response.json() if response.content else []

    async def delete(self, table: str, *, query: dict[str, str]) -> None:
        response = await self._client.delete(
            f"{self.base_url}/rest/v1/{quote(table, safe='')}",
            params=query,
            headers=self._headers("return=minimal"),
        )
        self._raise(response)

    async def rpc(self, function: str, payload: dict[str, Any]) -> Any:
        response = await self._client.post(
            f"{self.base_url}/rest/v1/rpc/{quote(function, safe='')}",
            json=payload,
            headers=self._headers(),
        )
        self._raise(response)
        return response.json() if response.content else None

    async def upload(self, bucket: str, path: str, content: bytes, content_type: str) -> dict[str, Any]:
        encoded_path = "/".join(quote(part, safe="") for part in path.strip("/").split("/"))
        response = await self._client.post(
            f"{self.base_url}/storage/v1/object/{quote(bucket, safe='')}/{encoded_path}",
            content=content,
            headers={**self._headers(), "Content-Type": content_type, "x-upsert": "false"},
        )
        self._raise(response)
        return response.json() if response.content else {}

    async def signed_url(self, bucket: str, path: str, expires_in: int = 600) -> str:
        encoded_path = "/".join(quote(part, safe="") for part in path.strip("/").split("/"))
        response = await self._client.post(
            f"{self.base_url}/storage/v1/object/sign/{quote(bucket, safe='')}/{encoded_path}",
            json={"expiresIn": expires_in},
            headers=self._headers(),
        )
        self._raise(response)
        data = response.json()
        signed = data.get("signedURL") or data.get("signedUrl")
        if not signed:
            raise RuntimeError("Supabase did not return a signed URL")
        return signed if signed.startswith("http") else f"{self.base_url}/storage/v1{signed}"

    async def download(self, bucket: str, path: str) -> bytes:
        encoded_path = "/".join(quote(part, safe="") for part in path.strip("/").split("/"))
        response = await self._client.get(
            f"{self.base_url}/storage/v1/object/{quote(bucket, safe='')}/{encoded_path}",
            headers=self._headers(),
        )
        self._raise(response)
        return response.content

    async def aclose(self) -> None:
        await self._client.aclose()

    @staticmethod
    def _raise(response: httpx.Response) -> None:
        if response.is_error:
            # Do not include authorization headers or request secrets in the raised detail.
            detail = response.text[:1000]
            raise httpx.HTTPStatusError(
                f"Supabase request failed ({response.status_code}): {detail}",
                request=response.request,
                response=response,
            )
