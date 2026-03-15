"""
异常处理中间件和全局异常处理器
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from .exceptions import YumiException

logger = logging.getLogger(__name__)


class ErrorResponse:
    """统一错误响应格式"""

    def __init__(
        self,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.details = details
        self.request_id = request_id

    def to_dict(self) -> dict[str, Any]:
        result = {
            "success": False,
            "error": {
                "code": self.code,
                "message": self.message,
            },
        }
        if self.details:
            result["error"]["details"] = self.details
        if self.request_id:
            result["error"]["request_id"] = self.request_id
        return result


def setup_exception_handlers(app: FastAPI) -> None:
    """注册全局异常处理器"""

    @app.exception_handler(YumiException)
    async def yumi_exception_handler(
        request: Request, exc: YumiException
    ) -> JSONResponse:
        logger.warning(
            "Yumi exception occurred: %s - %s",
            exc.code,
            exc.message,
            extra={"details": exc.details, "path": request.url.path},
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                code=exc.code,
                message=exc.message,
                details=exc.details,
            ).to_dict(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = []
        for error in exc.errors():
            errors.append(
                {
                    "field": ".".join(str(loc) for loc in error["loc"]),
                    "message": error["msg"],
                    "type": error["type"],
                }
            )

        logger.warning(
            "Validation error: %s",
            errors,
            extra={"path": request.url.path},
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                code="VALIDATION_ERROR",
                message="请求数据验证失败",
                details={"errors": errors},
            ).to_dict(),
        )

    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(
        request: Request, exc: ValidationError
    ) -> JSONResponse:
        errors = []
        for error in exc.errors():
            errors.append(
                {
                    "field": ".".join(str(loc) for loc in error["loc"]),
                    "message": error["msg"],
                    "type": error["type"],
                }
            )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                code="VALIDATION_ERROR",
                message="数据验证失败",
                details={"errors": errors},
            ).to_dict(),
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "Unhandled exception occurred: %s",
            str(exc),
            extra={"path": request.url.path},
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                code="INTERNAL_ERROR",
                message="服务器内部错误，请稍后再试",
            ).to_dict(),
        )
