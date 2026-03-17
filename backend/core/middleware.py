"""
Request Middleware - 请求追踪中间件
"""
from __future__ import annotations

import time
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .logging import YumiLogger, get_logger

logger = get_logger(__name__)


class RequestTracingMiddleware(BaseHTTPMiddleware):
    """请求追踪中间件 - 为每个请求生成唯一 ID 并记录请求日志"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = YumiLogger.set_request_id()

        start_time = time.time()

        logger.info(
            f"Request started: {request.method} {request.url.path}",
        )

        try:
            response = await call_next(request)

            duration_ms = (time.time() - start_time) * 1000

            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"- Status: {response.status_code} - Duration: {duration_ms:.2f}ms",
            )

            response.headers["X-Request-ID"] = request_id
            return response

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"- Duration: {duration_ms:.2f}ms - Error: {str(e)}",
            )
            raise

        finally:
            YumiLogger.clear_request_id()


class SlowRequestMiddleware(BaseHTTPMiddleware):
    """慢请求监控中间件 - 记录超过阈值的慢请求"""

    def __init__(self, app, threshold_ms: float = 1000):
        super().__init__(app)
        self.threshold_ms = threshold_ms

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        response = await call_next(request)

        duration_ms = (time.time() - start_time) * 1000

        if duration_ms > self.threshold_ms:
            logger.warning(
                f"Slow request detected: {request.method} {request.url.path} "
                f"- Duration: {duration_ms:.2f}ms (threshold: {self.threshold_ms}ms)",
            )

        return response
