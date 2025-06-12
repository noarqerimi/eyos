from typing import Awaitable

import pydantic_core._pydantic_core
from fastapi import Request, Response
from fastapi.responses import JSONResponse

from eyos.exceptions.base import ExceptionHandlers

exception_handler = ExceptionHandlers()


@exception_handler.add_exception_handler(pydantic_core._pydantic_core.ValidationError)
def handle_pydantic_validation_error(
    request: Request, exc: pydantic_core._pydantic_core.ValidationError
) -> Response | Awaitable[Response]:
    return JSONResponse(status_code=400, content={"message": "Validation error", "details": exc.errors()})
