"""Consistent JSON errors without request bodies or internal details."""

import uuid
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from fastapi.responses import JSONResponse


def install_handlers(api, logger):
    @api.exception_handler(HTTPException)
    async def http_error(request, exc):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "code": "http_error"},
            headers=exc.headers,
        )

    @api.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        errors = [
            {"loc": list(e["loc"]), "msg": e["msg"], "type": e["type"]}
            for e in exc.errors()
        ]
        return JSONResponse(
            status_code=422, content={"detail": errors, "code": "validation_error"}
        )

    @api.exception_handler(Exception)
    async def unexpected_error(request, exc):
        request_id = uuid.uuid4().hex
        logger.error(
            "API failure id=%s method=%s",
            request_id,
            request.method,
            exc_info=(type(exc), exc, exc.__traceback__),
        )
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "code": "internal_error",
                "request_id": request_id,
            },
        )
