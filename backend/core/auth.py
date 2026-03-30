"""
Authentication Dependencies - 认证依赖注入

提供 JWT Token 验证和用户认证的 FastAPI 依赖项
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from . import get_logger, settings
from ..services import auth_service

logger = get_logger(__name__)

security = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)]
) -> str | None:
    """
    从 Authorization Header 中获取当前用户 ID

    Args:
        credentials: HTTP Bearer Token 认证信息

    Returns:
        用户 ID，如果没有提供或 Token 无效则返回 None
    """
    if not credentials:
        return None

    try:
        token = credentials.credentials
        result = auth_service.jwt.verify_access_token(token)
        if result:
            user_id, _ = result
            return user_id
    except Exception as e:
        logger.debug("Token verification failed: %s", e)

    return None


async def require_current_user(
    current_user_id: Annotated[str | None, Depends(get_current_user_id)]
) -> str:
    """
    要求用户必须认证

    Args:
        current_user_id: 从依赖注入获取的当前用户 ID

    Returns:
        认证后的用户 ID

    Raises:
        HTTPException: 401 Unauthorized - 用户未认证
    """
    if not current_user_id:
        logger.debug("require_current_user: No user ID found, returning 401")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未授权，请先登录",
            headers={"WWW-Authenticate": "Bearer"},
        )
    logger.debug("require_current_user: Authenticated user_id=%s", current_user_id)
    return current_user_id


def validate_user_access(request_user_id: str, current_user_id: str) -> None:
    """
    验证用户是否有权限访问指定资源

    Args:
        request_user_id: 请求中的用户 ID
        current_user_id: 当前认证的用户 ID

    Raises:
        HTTPException: 403 Forbidden - 无权访问
    """
    logger.debug("validate_user_access: request_user_id=%s, current_user_id=%s", 
                 request_user_id, current_user_id)
    if request_user_id != current_user_id:
        logger.warning("validate_user_access: Access denied - IDs don't match!")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此资源"
        )
