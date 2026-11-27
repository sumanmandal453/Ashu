
from __future__ import annotations

from typing import Any
from urllib.parse import quote, urlparse

import httpx

from app.core.config import settings
from app.core.exceptions import IntegrationUnavailable


class DigiiCampusClient:
    """
    Read-only Digiicampus adapter for Ashu.

    Endpoint paths are configurable through environment variables.
    Requests remain disabled until:
    - DIGII_READONLY_ENABLED is true.
    - An authorized Digiicampus credential is configured.
    - The requested endpoint path is configured.

    No assignment submission or other write operation is implemented here.
    """

    def __init__(
        self,
        auth_token: str | None = None,
        external_student_id: str | None = None,
    ):
        self.base_url = settings.digii_base_url.rstrip("/")

        parsed = urlparse(self.base_url)

        if (
            parsed.scheme != "https"
            or parsed.hostname != settings.digii_allowed_host
        ):
            raise ValueError(
                "Digiicampus host is not on the configured allowlist"
            )

        self.auth_token = auth_token or settings.digii_auth_token
        self.external_student_id = external_student_id

        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(25.0),
            follow_redirects=False,
        )

    def _require_enabled(
        self,
        path: str | None,
        operation: str,
    ) -> str:
        """Validate integration configuration before making a request."""

        if not settings.digii_readonly_enabled:
            raise IntegrationUnavailable(
                "Digiicampus read-only integration is disabled"
            )

        if not self.auth_token:
            raise IntegrationUnavailable(
                "No authorized Digiicampus development credential is configured"
            )

        if not path:
            raise IntegrationUnavailable(
                f"No verified Bhawanipur endpoint configured for {operation}"
            )

        if not path.startswith("/") or path.startswith("//"):
            raise ValueError(
                "Digiicampus endpoint path must start with one /"
            )

        return path

    async def _get(
        self,
        path: str | None,
        operation: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Perform a validated read-only GET request."""

        verified_path = self._require_enabled(path, operation)

        # Auth-Token is the header documented by the independent
        # Digiicampus connector. Confirm this authentication method
        # with Bhawanipur before enabling live requests.
        headers = {
            "Auth-Token": self.auth_token or "",
            "Accept": "application/json",
        }

        response = await self.client.get(
            self.base_url + verified_path,
            params=params,
            headers=headers,
        )

        if response.status_code in (401, 403):
            raise IntegrationUnavailable(
                "Digiicampus rejected the configured credentials"
            )

        if response.status_code == 429:
            raise IntegrationUnavailable(
                "Digiicampus rate limit reached; retry later"
            )

        response.raise_for_status()

        try:
            return response.json()
        except ValueError as exc:
            raise IntegrationUnavailable(
                f"Digiicampus {operation} returned non-JSON content"
            ) from exc

    async def test_connection(self) -> dict[str, Any]:
        """Test connectivity using a configured profile endpoint."""

        data = await self._get(
            settings.digii_profile_path,
            "profile",
        )

        return {
            "connected": True,
            "profile": data,
        }

    async def get_profile(self) -> Any:
        """Retrieve the Digiicampus student profile."""

        return await self._get(
            settings.digii_profile_path,
            "profile",
        )

    async def get_courses(self) -> Any:
        """Retrieve the student's enrolled courses."""

        return await self._get(
            settings.digii_courses_path,
            "courses",
        )

    async def get_assignments(
        self,
        class_id: str,
        page: int = 1,
        page_size: int = 10,
    ) -> Any:
        """
        Retrieve assignments for a particular class.

        Bhawanipur's observed request uses:
            page=1
            perPage=10

        The classId and ukid path placeholders are replaced dynamically.
        """

        if not class_id:
            raise ValueError("Digiicampus class ID is required")

        if page < 1:
            raise ValueError("Page must be at least 1")

        if not 1 <= page_size <= 100:
            raise ValueError("Page size must be between 1 and 100")

        path = self._require_enabled(
            settings.digii_assignments_path,
            "assignments",
        )

        # Replace dynamic URL path parameters.
        if "{classId}" in path:
            path = path.replace(
                "{classId}",
                quote(str(class_id), safe=""),
            )

        if "{ukid}" in path:
            if not self.external_student_id:
                raise IntegrationUnavailable(
                    "Digiicampus external student identifier is missing"
                )

            path = path.replace(
                "{ukid}",
                quote(str(self.external_student_id), safe=""),
            )

        # Match the pagination parameter names observed in Bhawanipur.
        params = {
            "page": page,
            "perPage": page_size,
        }

        # If the configured endpoint does not contain classId in its
        # path, pass it as a query parameter.
        if "{classId}" not in settings.digii_assignments_path:
            params["classId"] = class_id

        return await self._get(
            path,
            "assignments",
            params,
        )

    async def get_assignment_details(
        self,
        assignment_id: str,
        class_id: str,
    ) -> Any:
        """
        Retrieve an individual assignment.

        Bhawanipur's observed endpoint:
        /rest/assignments/v1/getStudentAssignmentDetails

        Query parameters:
        assignmentId
        classId
        """

        if not assignment_id or not class_id:
            raise ValueError(
                "Both assignment ID and class ID are required"
            )

        return await self._get(
            settings.digii_assignment_detail_path,
            "assignment details",
            {
                "assignmentId": assignment_id,
                "classId": class_id,
            },
        )

    async def get_resources(self, class_id: str) -> Any:
        """Retrieve course resources when a verified path is configured."""

        return await self._get(
            settings.digii_resources_path,
            "resources",
            {
                "classId": class_id,
            },
        )

    async def get_course_modules(self, class_id: str) -> Any:
        """Retrieve course modules when a verified path is configured."""

        return await self._get(
            settings.digii_modules_path,
            "course modules",
            {
                "classId": class_id,
            },
        )

    async def get_course_sessions(self, class_id: str) -> Any:
        """Retrieve course sessions when a verified path is configured."""

        return await self._get(
            settings.digii_sessions_path,
            "course sessions",
            {
                "classId": class_id,
            },
        )

    async def get_feed(self) -> Any:
        """Retrieve the college feed."""

        return await self._get(
            settings.digii_feed_path,
            "feed",
        )

    async def get_calendar_events(self) -> Any:
        """Retrieve institutional calendar events."""

        return await self._get(
            settings.digii_calendar_path,
            "calendar",
        )

    async def get_notifications(self) -> Any:
        """Retrieve college notifications."""

        return await self._get(
            settings.digii_notifications_path,
            "notifications",
        )

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""

        await self.client.aclose()

