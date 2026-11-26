import asyncio
import logging
from app.core.config import settings
from app.workers.worker import run_worker

logging.basicConfig(level=settings.log_level)
asyncio.run(run_worker())
