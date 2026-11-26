from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import analytics, assignments, calendar, courses, dashboard, documents, integrations, materials, notifications, settings as settings_api, submissions, subjects, users, webhooks
from app.core.config import settings
from app.core.logging import configure_logging

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Ashu API starting in %s mode", settings.app_env)
    yield
    logger.info("Ashu API stopped")


app = FastAPI(
    title="Ashu API",
    version="0.1.0",
    description="Backend services for Ashu academic assignment automation",
    lifespan=lifespan,
    docs_url="/docs" if settings.app_env != "production" else None,
    redoc_url="/redoc" if settings.app_env != "production" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "apikey", "x-client-info"],
)

for router in [users.router, assignments.router, dashboard.router, courses.router, subjects.router,
               integrations.router, analytics.router, materials.router, documents.router,
               submissions.router, notifications.router, calendar.router, settings_api.router]:
    app.include_router(router, prefix=settings.api_prefix)
app.include_router(webhooks.router, prefix=settings.api_prefix)


@app.get("/health/live", tags=["health"])
async def live():
    return {"status": "ok", "service": "ashu-api"}


@app.get("/health/ready", tags=["health"])
async def ready():
    missing = []
    if not settings.supabase_url: missing.append("SUPABASE_URL")
    if not settings.supabase_publishable_key: missing.append("SUPABASE_PUBLISHABLE_KEY")
    if not settings.clerk_secret_key: missing.append("CLERK_SECRET_KEY")
    return JSONResponse(status_code=200 if not missing else 503, content={"ready": not missing, "missing_configuration": missing})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled backend exception at %s", request.url.path)
    return JSONResponse(status_code=500, content={"success": False, "error": {"code": "internal_error", "message": "An unexpected server error occurred"}})
