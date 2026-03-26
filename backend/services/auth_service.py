"""
Authentication Service - 认证服务

提供：
- 密码加密和验证
- JWT Token 生成和验证
- 昵称和密码验证
"""

from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

from ..core import get_logger, settings

logger = get_logger(__name__)


class PasswordService:
    """密码服务 - 处理密码的加密和验证"""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        加密密码

        Args:
            password: 明文密码

        Returns:
            加密后的密码哈希
        """
        password_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        验证密码

        Args:
            password: 明文密码
            password_hash: 存储的密码哈希

        Returns:
            密码是否匹配
        """
        try:
            password_bytes = password.encode("utf-8")
            hash_bytes = password_hash.encode("utf-8")
            return bcrypt.checkpw(password_bytes, hash_bytes)
        except ValueError as e:
            logger.error("Invalid password hash format: %s", e)
            return False
        except Exception as e:
            logger.error("Password verification error: %s", e)
            raise


class ValidationError(Exception):
    """验证错误"""
    pass


class ValidatorService:
    """验证服务 - 处理昵称和密码的验证"""

    NICKNAME_MIN_LENGTH = 2
    NICKNAME_MAX_LENGTH = 20
    NICKNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_\u4e00-\u9fa5]+$")

    PASSWORD_MIN_LENGTH = 6
    PASSWORD_MAX_LENGTH = 128

    @classmethod
    def validate_nickname(cls, nickname: str) -> tuple[bool, str]:
        """
        验证昵称

        Args:
            nickname: 昵称

        Returns:
            (是否有效, 错误信息)
        """
        if not nickname or not nickname.strip():
            return False, "昵称不能为空"

        nickname = nickname.strip()

        if len(nickname) < cls.NICKNAME_MIN_LENGTH:
            return False, f"昵称长度不能少于 {cls.NICKNAME_MIN_LENGTH} 个字符"

        if len(nickname) > cls.NICKNAME_MAX_LENGTH:
            return False, f"昵称长度不能超过 {cls.NICKNAME_MAX_LENGTH} 个字符"

        if not cls.NICKNAME_PATTERN.match(nickname):
            return False, "昵称只能包含字母、数字、下划线和中文"

        return True, ""

    @classmethod
    def validate_password(cls, password: str) -> tuple[bool, str]:
        """
        验证密码强度

        Args:
            password: 密码

        Returns:
            (是否有效, 错误信息)
        """
        if not password:
            return False, "密码不能为空"

        if len(password) < cls.PASSWORD_MIN_LENGTH:
            return False, f"密码长度不能少于 {cls.PASSWORD_MIN_LENGTH} 个字符"

        if len(password) > cls.PASSWORD_MAX_LENGTH:
            return False, f"密码长度不能超过 {cls.PASSWORD_MAX_LENGTH} 个字符"

        return True, ""


class JWTService:
    """JWT Token 服务 - 处理 Token 的生成和验证"""

    def __init__(self):
        self.secret_key = settings.jwt.secret_key
        self.algorithm = settings.jwt.algorithm
        self.access_token_expire_minutes = settings.jwt.access_token_expire_minutes
        self.refresh_token_expire_days = settings.jwt.refresh_token_expire_days
        self._blacklist: set[str] = set()

    def generate_access_token(self, user_id: str, nickname: str) -> str:
        """
        生成访问 Token

        Args:
            user_id: 用户 ID (UUID)
            nickname: 用户昵称

        Returns:
            JWT Access Token
        """
        expire = datetime.now(UTC) + timedelta(minutes=self.access_token_expire_minutes)
        payload = {
            "sub": user_id,
            "nickname": nickname,
            "type": "access",
            "exp": expire,
            "iat": datetime.now(UTC)
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def generate_refresh_token(self, user_id: str) -> str:
        """
        生成刷新 Token

        Args:
            user_id: 用户 ID (UUID)

        Returns:
            JWT Refresh Token
        """
        expire = datetime.now(UTC) + timedelta(days=self.refresh_token_expire_days)
        payload = {
            "sub": user_id,
            "type": "refresh",
            "exp": expire,
            "iat": datetime.now(UTC)
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def blacklist_token(self, token: str) -> None:
        """
        将 Token 加入黑名单

        Args:
            token: JWT Token
        """
        self._blacklist.add(token)
        logger.debug("Token added to blacklist")

    def verify_token(self, token: str) -> dict[str, Any] | None:
        """
        验证 Token 并返回 payload

        Args:
            token: JWT Token

        Returns:
            Token payload，无效则返回 None
        """
        if token in self._blacklist:
            logger.debug("Token is blacklisted")
            return None

        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": True}
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.debug("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.debug("Invalid token: %s", e)
            return None

    def verify_access_token(self, token: str) -> tuple[str, str] | None:
        """
        验证访问 Token

        Args:
            token: JWT Access Token

        Returns:
            (user_id, nickname)，无效则返回 None
        """
        payload = self.verify_token(token)
        if not payload or payload.get("type") != "access":
            return None
        user_id = payload.get("sub")
        nickname = payload.get("nickname")
        if not user_id or not nickname:
            return None
        return user_id, nickname

    def verify_refresh_token(self, token: str) -> str | None:
        """
        验证刷新 Token

        Args:
            token: JWT Refresh Token

        Returns:
            user_id，无效则返回 None
        """
        payload = self.verify_token(token)
        if not payload or payload.get("type") != "refresh":
            return None
        return payload.get("sub")

    def refresh_tokens(self, refresh_token: str, nickname: str) -> tuple[str, str] | None:
        """
        使用刷新 Token 获取新的访问 Token 和刷新 Token

        Args:
            refresh_token: 刷新 Token
            nickname: 用户昵称

        Returns:
            (new_access_token, new_refresh_token)，无效则返回 None
        """
        user_id = self.verify_refresh_token(refresh_token)
        if not user_id:
            return None
        new_access_token = self.generate_access_token(user_id, nickname)
        new_refresh_token = self.generate_refresh_token(user_id)
        return new_access_token, new_refresh_token


class AuthService:
    """综合认证服务"""

    def __init__(self):
        self.password = PasswordService()
        self.validator = ValidatorService()
        self.jwt = JWTService()

    def generate_user_id(self) -> str:
        """
        生成用户 UUID

        Returns:
            UUID 字符串
        """
        return str(uuid.uuid4())

    async def register_user(
        self,
        nickname: str,
        password: str
    ) -> tuple[str, str, str]:
        """
        注册新用户

        Args:
            nickname: 昵称
            password: 密码

        Returns:
            (user_id, access_token, refresh_token)

        Raises:
            ValidationError: 验证失败时抛出
        """
        is_valid, error = self.validator.validate_nickname(nickname)
        if not is_valid:
            raise ValidationError(error)

        is_valid, error = self.validator.validate_password(password)
        if not is_valid:
            raise ValidationError(error)

        from ..database_sqlmodel import get_session
        from sqlmodel import select
        from ..models import User

        async with get_session() as session:
            result = await session.exec(select(User).where(User.nickname == nickname))
            existing_user = result.first()

            if existing_user:
                raise ValidationError("该昵称已被使用")

            user_id = self.generate_user_id()
            password_hash = self.password.hash_password(password)

            new_user = User(
                id=user_id,
                nickname=nickname,
                password_hash=password_hash,
                role_name="Yumi",
                preferences_json='{"communication_style": "warm", "topics_of_interest": ["生活", "工作", "情感"], "emotional_support_level": "high", "response_length": "medium"}'
            )
            session.add(new_user)
            await session.commit()

        access_token = self.jwt.generate_access_token(user_id, nickname)
        refresh_token = self.jwt.generate_refresh_token(user_id)

        logger.info("User registered: user_id=%s, nickname=%s", user_id, nickname)
        return user_id, access_token, refresh_token

    async def login_user(
        self,
        nickname: str,
        password: str
    ) -> tuple[str, str, str] | None:
        """
        用户登录

        Args:
            nickname: 昵称
            password: 密码

        Returns:
            (user_id, access_token, refresh_token)，登录失败返回 None
        """
        from ..database_sqlmodel import get_session
        from sqlmodel import select
        from ..models import User

        async with get_session() as session:
            result = await session.exec(select(User).where(User.nickname == nickname))
            user = result.first()

            if not user:
                logger.debug("Login failed: nickname not found")
                return None

            if not user.password_hash:
                logger.debug("Login failed: user has no password")
                return None

            if not self.password.verify_password(password, user.password_hash):
                logger.debug("Login failed: password mismatch")
                return None

        access_token = self.jwt.generate_access_token(user.id, nickname)
        refresh_token = self.jwt.generate_refresh_token(user.id)

        logger.info("User logged in: user_id=%s, nickname=%s", user.id, nickname)
        return user.id, access_token, refresh_token


auth_service = AuthService()
