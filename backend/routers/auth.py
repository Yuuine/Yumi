"""
Authentication API Router - 认证 API 路由

提供：
- 用户注册
- 用户登录
- Token 刷新
- 获取当前用户信息
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from ..core import get_logger
from ..database_sqlmodel import get_session
from ..services import ValidationError, auth_service
from ..services.character_card import insert_character_card
from ..services.log_service import AuditAction, log_service

router = APIRouter()
logger = get_logger(__name__)
security = HTTPBearer()


class RegisterRequest(BaseModel):
    """注册请求"""
    nickname: str = Field(..., description="用户昵称", min_length=2, max_length=20)
    password: str = Field(..., description="用户密码", min_length=6, max_length=128)


class LoginRequest(BaseModel):
    """登录请求"""
    nickname: str = Field(..., description="用户昵称")
    password: str = Field(..., description="用户密码")


class TokenResponse(BaseModel):
    """Token 响应"""
    userId: str = Field(..., alias="userId")
    accessToken: str = Field(..., alias="accessToken")
    refreshToken: str = Field(..., alias="refreshToken")
    nickname: str = Field(..., alias="nickname")

    class Config:
        populate_by_name = True


class RefreshTokenRequest(BaseModel):
    """刷新 Token 请求"""
    refreshToken: str = Field(..., alias="refreshToken")

    class Config:
        populate_by_name = True


class UserInfoResponse(BaseModel):
    """用户信息响应"""
    userId: str = Field(..., alias="userId")
    nickname: str

    class Config:
        populate_by_name = True


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> tuple[str, str]:
    """
    从 Authorization Header 获取当前用户

    Returns:
        (user_id, nickname)

    Raises:
        HTTPException: 认证失败时抛出
    """
    token = credentials.credentials
    result = auth_service.jwt.verify_access_token(token)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的访问令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return result


@router.post("/auth/register", response_model=TokenResponse)
async def register(request: RegisterRequest, req: Request):
    """
    用户注册

    创建新用户账号，自动创建默认角色"艾拉"，返回访问令牌和刷新令牌
    """
    try:
        user_id, access_token, refresh_token = await auth_service.register_user(
            nickname=request.nickname,
            password=request.password
        )

        # 自动为新用户创建默认角色"艾拉"
        try:
            async with get_session() as session:
                await insert_character_card(
                    session=session,
                    user_id=user_id,
                    card_data=None  # 使用默认艾拉角色数据
                )
                logger.info("Default character 'Aira' created for user: %s", user_id)
        except Exception as char_error:
            # 角色创建失败不影响注册成功，记录日志即可
            logger.error("Failed to create default character for user %s: %s", user_id, char_error)

        await log_service.log_audit(
            action=AuditAction.USER_REGISTER,
            resource_type="user",
            resource_id=user_id,
            result="SUCCESS",
            user_id=user_id,
            details={"nickname": request.nickname}
        )

        return TokenResponse(
            userId=user_id,
            accessToken=access_token,
            refreshToken=refresh_token,
            nickname=request.nickname
        )

    except ValidationError as e:
        await log_service.log_audit(
            action=AuditAction.USER_REGISTER,
            resource_type="user",
            resource_id="",
            result="FAIL",
            user_id="",
            details={"error": str(e), "nickname": request.nickname}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(e), "code": "VALIDATION_ERROR"}
        ) from e

    except Exception as e:
        logger.error("Registration failed: %s", e, exc_info=True)
        await log_service.log_audit(
            action=AuditAction.USER_REGISTER,
            resource_type="user",
            resource_id="",
            result="FAIL",
            user_id="",
            details={"error": str(e), "nickname": request.nickname}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册失败，请稍后重试"
        ) from e


@router.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest, req: Request):
    """
    用户登录

    使用昵称和密码登录，返回访问令牌和刷新令牌
    """
    result = await auth_service.login_user(
        nickname=request.nickname,
        password=request.password
    )

    if not result:
        await log_service.log_audit(
            action=AuditAction.USER_LOGIN,
            resource_type="user",
            resource_id="",
            result="FAIL",
            user_id="",
            details={"nickname": request.nickname, "reason": "invalid_credentials"}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="昵称或密码错误"
        )

    user_id, access_token, refresh_token = result

    await log_service.log_audit(
        action=AuditAction.USER_LOGIN,
        resource_type="user",
        resource_id=user_id,
        result="SUCCESS",
        user_id=user_id,
        details={"nickname": request.nickname}
    )

    return TokenResponse(
        userId=user_id,
        accessToken=access_token,
        refreshToken=refresh_token,
        nickname=request.nickname
    )


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest, req: Request):
    """
    刷新访问令牌

    使用刷新令牌获取新的访问令牌和刷新令牌
    """
    user_id = auth_service.jwt.verify_refresh_token(request.refreshToken)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌"
        )

    from ..database_sqlmodel import get_session
    from sqlmodel import select
    from ..models import User

    async with get_session() as session:
        result = await session.exec(select(User).where(User.id == user_id))
        user = result.first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        nickname = user.nickname

    new_access_token, new_refresh_token = auth_service.jwt.refresh_tokens(
        request.refreshToken,
        nickname
    )

    if not new_access_token or not new_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="刷新令牌已过期或无效"
        )

    return TokenResponse(
        userId=user_id,
        accessToken=new_access_token,
        refreshToken=new_refresh_token,
        nickname=nickname
    )


@router.get("/auth/me", response_model=UserInfoResponse)
async def get_current_user_info(
    user_credentials: tuple[str, str] = Depends(get_current_user)
):
    """
    获取当前登录用户信息
    """
    user_id, nickname = user_credentials
    from ..database_sqlmodel import get_session
    from sqlmodel import select
    from ..models import User

    async with get_session() as session:
        result = await session.exec(select(User).where(User.id == user_id))
        user = result.first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

    return UserInfoResponse(
        userId=user_id,
        nickname=nickname
    )
