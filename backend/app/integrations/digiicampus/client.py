from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlparse

import httpx

from app.core.config import settings
from app.core.exceptions import IntegrationUnavailable

logger = logging.getLogger(__name__)


class DigiiCampusClient:
    """Read-only Digiicampus adapter.

    IMPORTANT: All endpoint paths are explicitly configurable and default to None.
    This intentionally prevents unverified candidate endpoints from being called on
    Bhawanipur. Enable only after confirming the endpoint and access method with the
    institution and a real response from this tenant.
    """

    def __init__(self, auth_token: str | None = None, external_student_id: str | None = None):
        self.base_url = settings.digii_base_url.rstrip("/")
        parsed = urlparse(self.base_url)
        if parsed.scheme != "https" or parsed.hostname != settings.digii_allowed_host:
            raise ValueError("Digiicampus host is not on the configured allowlist")
        self.auth_token = auth_token or settings.digii_auth_token
        self.external_student_id = external_student_id
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(25.0), follow_redirects=False)

    def _require_enabled(self, path: str | None, operation: str) -> str:
        if not settings.digii_readonly_enabled:
            raise IntegrationUnavailable("Digiicampus read-only integration is disabled")
        if not self.auth_token:
            raise IntegrationUnavailable("No authorized Digiicampus development credential is configured")
        if not path:
            raise IntegrationUnavailable(
                f"No verified Bhawanipur endpoint configured for {operation}; endpoint discovery is required"
            )
        if not path.startswith("/") or path.startswith("//"):
            raise ValueError("Digiicampus endpoint path must be a relative absolute-path")
        return path

    async def _get(self, path: str | None, operation: str, params: dict[str, Any] | None = None) -> Any:
        verified_path = self._require_enabled(path, operation)
        headers = {"Auth-Token": self.auth_token or "", "Accept": "application/json"}
        response = await self.client.get(self.base_url + verified_path, params=params, headers=headers)
        if response.status_code in (401, 403):
            raise IntegrationUnavailable("Digiicampus rejected the configured credentials")
        if response.status_code == 429:
            raise IntegrationUnavailable("Digiicampus rate limit reached; retry later")
        response.raise_for_status()
        try:
            return response.json()
        except ValueError as exc:
            raise IntegrationUnavailable(f"Digiicampus {operation} returned non-JSON content") from exc

    async def test_connection(self) -> dict[str, Any]:
        data = await self._get(settings.digii_profile_path, "profile")
        return {"connected": True, "profile": data}

    async def get_profile(self) -> Any:
        return await self._get(settings.digii_profile_path, "profile")

    async def get_courses(self) -> Any:
        return await self._get(settings.digii_courses_path, "courses")

    async def get_assignments(self, class_id: str, page: int = 1, page_size: int = 50) -> Any:
        path = self._require_enabled(settings.digii_assignments_path, "assignments")
        if "{classId}" in path or "{ukid}" in path:
            if not self.external_student_id and "{ukid}" in path:
                raise IntegrationUnavailable("Digiicampus external student identifier is missing")
            path = path.replace("{classId}", httpx.URL("https://x/" + class_id).path.lstrip("/"))
            path = path.replace("{ukid}", httpx.URL("https://x/" + (self.external_student_id or "")).path.lstrip("/"))
            return await self._get(path, "assignments", {"page": page, "pageSize": page_size})
        return await self._get(path, "assignments", {"classId": class_id, "page": page, "pageSize": page_size})

    async def get_assignment_details(self, assignment_id: str, class_id: str) -> Any:
        return await self._get(
            settings.digii_assignment_detail_path,
            "assignment details",
            {"assignmentId": assignment_id, "classId": class_id},
        )

    async def get_resources(self, class_id: str) -> Any:
        return await self._get(settings.digii_resources_path, "resources", {"classId": class_id})

    async def get_course_modules(self, class_id: str) -> Any:
        return await self._get(settings.digii_modules_path, "course modules", {"classId": class_id})

    async def get_course_sessions(self, class_id: str) -> Any:
        return await self._get(settings.digii_sessions_path, "course sessions", {"classId": class_id})

    async def get_feed(self) -> Any:
        return await self._get(settings.digii_feed_path, "feed")

    async def get_calendar_events(self) -> Any:
        return await self._get(settings.digii_calendar_path, "calendar")

    async def get_notifications(self) -> Any:
        return await self._get(settings.digii_notifications_path, "notifications")

    async def aclose(self) -> None:
        await self.client.aclose()
