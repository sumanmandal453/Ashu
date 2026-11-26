from fastapi import HTTPException, status


class IntegrationUnavailable(Exception):
    pass


class ExternalServiceError(Exception):
    pass


def not_configured(name: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"{name} is not configured. Complete its server-side setup first.",
    )
