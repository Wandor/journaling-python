from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.status import HTTP_400_BAD_REQUEST
from app.core.logger import logger


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc.errors()}")

    formatted_errors = {}
    for error in exc.errors():
        path = ".".join(str(p) for p in error["loc"][1:])
        formatted_errors[path] = error["msg"]

    return JSONResponse(
        status_code=HTTP_400_BAD_REQUEST,
        content={
            "message": "Validation error",
            "errors": formatted_errors
        },
    )
