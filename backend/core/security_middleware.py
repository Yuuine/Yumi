"""
Security Headers Middleware - 安全响应头中间件

添加安全相关的 HTTP 响应头，防止常见的安全漏洞
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    安全响应头中间件

    添加以下安全头：
    - X-Content-Type-Options: nosniff - 防止 MIME 类型嗅探
    - X-Frame-Options: DENY - 防止点击劫持
    - Content-Security-Policy - 内容安全策略
    - X-XSS-Protection - XSS 保护（现代浏览器已内置，但为旧浏览器保留）
    - Referrer-Policy - 引用策略
    """

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self' ws: wss:; "
            "frame-src 'none'; "
            "object-src 'none'; "
            "base-uri 'self'"
        )

        return response
