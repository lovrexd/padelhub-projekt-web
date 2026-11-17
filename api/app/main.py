from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import Settings, settings
from app.core.errors import (
    AppError,
    app_error_handler,
    http_exception_handler,
    validation_error_handler,
)
from app.core.logging import setup_logging
from app.routers.auth import router as auth_router
from app.routers.bookings import router as bookings_router
from app.routers.courts import router as courts_router
from app.routers.health import router as health_router
from app.routers.matches import router as matches_router


def create_app(config: Settings = settings) -> FastAPI:
    """Tvornica FastAPI aplikacije — spaja konfiguraciju, greške i rute."""
    setup_logging(debug=config.ENV == "dev")
    app = FastAPI(title=config.APP_NAME, debug=config.ENV == "dev")

    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)

    app.include_router(health_router, prefix="/health", tags=["health"])
    app.include_router(auth_router, prefix="/auth", tags=["auth"])
    app.include_router(courts_router, prefix="/courts", tags=["courts"])
    app.include_router(bookings_router, prefix="/bookings", tags=["bookings"])
    app.include_router(matches_router, prefix="/matches", tags=["matches"])
    return app


app = create_app()
