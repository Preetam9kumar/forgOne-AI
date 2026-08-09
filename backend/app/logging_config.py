from __future__ import annotations

import logging
import os

from app.config import settings


def configure_logging() -> None:
    logging.basicConfig(level=settings.log_level, format=settings.log_format)
    logging.getLogger("uvicorn").handlers = logging.getLogger().handlers
    logging.getLogger("uvicorn.error").setLevel(settings.log_level)
    logging.getLogger("uvicorn.access").setLevel(settings.log_level)

    if settings.sentry_dsn:
        try:
            import sentry_sdk
            sentry_sdk.init(
                dsn=settings.sentry_dsn,
                environment=settings.environment,
                traces_sample_rate=0.1,
            )
            logging.getLogger("app").info("Sentry configured")
        except ImportError:
            logging.getLogger("app").warning(
                "SENTRY_DSN is set but sentry-sdk is not installed. Install sentry-sdk to enable error tracking."
            )
