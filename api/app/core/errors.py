from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    """Domenska greška koju bacaju servisi, a handler je pretvara u JSON odgovor.

    code je kratki identifikator za frontend/testove, message poruka za korisnika.
    """

    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code


async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    """Pretvara AppError u jedinstveni JSON format pogreške."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message},
    )


async def validation_error_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Pretvara Pydantic/FastAPI 422 pogreške u isti format uz popis polja."""
    errors = []
    for err in exc.errors():
        loc = [str(part) for part in err["loc"] if part != "body"]
        message = err["msg"].removeprefix("Value error, ")
        errors.append({"field": ".".join(loc), "message": message})
    return JSONResponse(
        status_code=422,
        content={
            "code": "validation_error",
            "message": "Neispravni podatci u zahtjevu",
            "errors": errors,
        },
    )


HTTP_ERROR_CODES = {404: "not_found", 405: "method_not_allowed"}


async def http_exception_handler(
    _request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Hvata greške samog frameworka (npr. nepostojeći URL) u isti format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": HTTP_ERROR_CODES.get(exc.status_code, "http_error"),
            "message": str(exc.detail),
        },
        headers=getattr(exc, "headers", None),
    )
