from typing import Any, Optional

import msgspec
from litestar import Request, Response
from litestar.exceptions import HTTPException
from litestar.status_codes import HTTP_500_INTERNAL_SERVER_ERROR

from src.log_config import get_logger

LOG = get_logger(__name__)


class ExceptionResponseBody(msgspec.Struct, frozen=True, kw_only=True, rename="camel"):
    status_code: int
    detail: str
    extra: Optional[dict[str, Any] | list[Any]] = None


class ExceptionResponse(Response[Any]):
    def __init__(self, body: ExceptionResponseBody) -> None:
        super().__init__(
            status_code=body.status_code,
            content={"statusCode": body.status_code, "detail": body.detail, "extra": body.extra if body.extra else {}},
        )


class AppError(Exception): ...


def app_exception_handler(request: Request[Any, Any, Any], exception: Exception) -> ExceptionResponse:
    match exception:
        case HTTPException():
            response = ExceptionResponse(
                ExceptionResponseBody(
                    status_code=exception.status_code,
                    detail=exception.detail,
                    extra=exception.extra,
                )
            )
        case _:
            response = ExceptionResponse(
                ExceptionResponseBody(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
            )

    LOG.info("HERE")
    LOG.error(exception, exc_info=exception)
    return response
