from __future__ import annotations

from app.core.exceptions import IntegrationUnavailable


class SubmissionProvider:
    async def validate_submission(self, *args, **kwargs):
        raise NotImplementedError

    async def submit_assignment(self, *args, **kwargs):
        raise NotImplementedError

    async def get_submission_status(self, *args, **kwargs):
        raise NotImplementedError


class DigiicampusSubmissionProvider(SubmissionProvider):
    async def validate_submission(self, *args, **kwargs):
        raise IntegrationUnavailable("Digiicampus assignment-upload mechanism is not verified or enabled")

    async def submit_assignment(self, *args, **kwargs):
        raise IntegrationUnavailable("Automatic assignment submission is disabled pending an authorized upload integration")

    async def get_submission_status(self, *args, **kwargs):
        raise IntegrationUnavailable("Portal submission-status retrieval is not configured")
