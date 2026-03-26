"""
Authentication Service Tests - 认证服务测试
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from backend.services.auth_service import (
    PasswordService,
    ValidatorService,
    JWTService,
    AuthService,
    ValidationError
)


class TestPasswordService:
    """测试密码服务"""

    def test_hash_password(self):
        """测试密码加密"""
        password = "test_password_123"
        hashed = PasswordService.hash_password(password)

        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password_correct(self):
        """测试验证正确密码"""
        password = "test_password_123"
        hashed = PasswordService.hash_password(password)

        assert PasswordService.verify_password(password, hashed) is True

    def test_verify_password_wrong(self):
        """测试验证错误密码"""
        password = "test_password_123"
        hashed = PasswordService.hash_password(password)

        assert PasswordService.verify_password("wrong_password", hashed) is False


class TestValidatorService:
    """测试验证服务"""

    def test_validate_nickname_valid(self):
        """测试验证有效昵称"""
        is_valid, error = ValidatorService.validate_nickname("测试用户")
        assert is_valid is True
        assert error == ""

    def test_validate_nickname_empty(self):
        """测试验证空昵称"""
        is_valid, error = ValidatorService.validate_nickname("")
        assert is_valid is False
        assert "不能为空" in error

    def test_validate_nickname_too_short(self):
        """测试验证太短的昵称"""
        is_valid, error = ValidatorService.validate_nickname("a")
        assert is_valid is False
        assert "不能少于" in error

    def test_validate_nickname_too_long(self):
        """测试验证太长的昵称"""
        long_name = "a" * 21
        is_valid, error = ValidatorService.validate_nickname(long_name)
        assert is_valid is False
        assert "不能超过" in error

    def test_validate_nickname_invalid_chars(self):
        """测试验证包含非法字符的昵称"""
        is_valid, error = ValidatorService.validate_nickname("test@user")
        assert is_valid is False
        assert "只能包含" in error

    def test_validate_password_valid(self):
        """测试验证有效密码"""
        is_valid, error = ValidatorService.validate_password("password123")
        assert is_valid is True
        assert error == ""

    def test_validate_password_empty(self):
        """测试验证空密码"""
        is_valid, error = ValidatorService.validate_password("")
        assert is_valid is False
        assert "不能为空" in error

    def test_validate_password_too_short(self):
        """测试验证太短的密码"""
        is_valid, error = ValidatorService.validate_password("12345")
        assert is_valid is False
        assert "不能少于" in error


class TestJWTService:
    """测试 JWT 服务"""

    def test_generate_access_token(self):
        """测试生成访问 Token"""
        jwt_service = JWTService()
        token = jwt_service.generate_access_token("user-123", "测试用户")

        assert token is not None
        assert len(token) > 0

    def test_generate_refresh_token(self):
        """测试生成刷新 Token"""
        jwt_service = JWTService()
        token = jwt_service.generate_refresh_token("user-123")

        assert token is not None
        assert len(token) > 0

    def test_verify_access_token_valid(self):
        """测试验证有效的访问 Token"""
        jwt_service = JWTService()
        token = jwt_service.generate_access_token("user-123", "测试用户")
        result = jwt_service.verify_access_token(token)

        assert result is not None
        assert result[0] == "user-123"
        assert result[1] == "测试用户"

    def test_verify_access_token_invalid(self):
        """测试验证无效的访问 Token"""
        jwt_service = JWTService()
        result = jwt_service.verify_access_token("invalid.token.here")

        assert result is None

    def test_verify_refresh_token_valid(self):
        """测试验证有效的刷新 Token"""
        jwt_service = JWTService()
        token = jwt_service.generate_refresh_token("user-123")
        result = jwt_service.verify_refresh_token(token)

        assert result == "user-123"

    def test_refresh_tokens(self):
        """测试刷新 Token"""
        jwt_service = JWTService()
        refresh_token = jwt_service.generate_refresh_token("user-123")

        result = jwt_service.refresh_tokens(refresh_token, "测试用户")

        assert result is not None
        new_access, new_refresh = result
        assert new_access is not None
        assert new_refresh is not None
        assert new_access != refresh_token


class TestAuthService:
    """测试综合认证服务"""

    @pytest.mark.asyncio
    @patch("backend.database.get_db")
    async def test_register_user_success(self, mock_get_db):
        """测试成功注册用户"""
        mock_db = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = None
        mock_db.execute.return_value = mock_cursor
        mock_get_db.return_value.__aenter__.return_value = mock_db

        auth_svc = AuthService()
        result = await auth_svc.register_user("新用户", "password123")

        assert result is not None
        user_id, access_token, refresh_token = result
        assert user_id is not None
        assert access_token is not None
        assert refresh_token is not None

    @pytest.mark.asyncio
    @patch("backend.database.get_db")
    async def test_register_user_duplicate_nickname(self, mock_get_db):
        """测试昵称已存在时注册失败"""
        mock_db = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = ("existing-id",)
        mock_db.execute.return_value = mock_cursor
        mock_get_db.return_value.__aenter__.return_value = mock_db

        auth_svc = AuthService()

        with pytest.raises(ValidationError, match="已被使用"):
            await auth_svc.register_user("已存在的用户", "password123")

    @pytest.mark.asyncio
    async def test_register_user_invalid_nickname(self):
        """测试昵称无效时注册失败"""
        auth_svc = AuthService()

        with pytest.raises(ValidationError, match="不能为空"):
            await auth_svc.register_user("", "password123")

    @pytest.mark.asyncio
    @patch("backend.database.get_db")
    async def test_login_user_success(self, mock_get_db):
        """测试成功登录"""
        auth_svc = AuthService()
        password_hash = auth_svc.password.hash_password("password123")

        mock_db = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = ("user-123", password_hash)
        mock_db.execute.return_value = mock_cursor
        mock_get_db.return_value.__aenter__.return_value = mock_db

        result = await auth_svc.login_user("测试用户", "password123")

        assert result is not None
        user_id, access_token, refresh_token = result
        assert user_id == "user-123"
        assert access_token is not None
        assert refresh_token is not None

    @pytest.mark.asyncio
    @patch("backend.database.get_db")
    async def test_login_user_not_found(self, mock_get_db):
        """测试用户不存在时登录失败"""
        mock_db = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = None
        mock_db.execute.return_value = mock_cursor
        mock_get_db.return_value.__aenter__.return_value = mock_db

        auth_svc = AuthService()
        result = await auth_svc.login_user("不存在的用户", "password123")

        assert result is None

    @pytest.mark.asyncio
    @patch("backend.database.get_db")
    async def test_login_user_wrong_password(self, mock_get_db):
        """测试密码错误时登录失败"""
        auth_svc = AuthService()
        password_hash = auth_svc.password.hash_password("correct_password")

        mock_db = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = ("user-123", password_hash)
        mock_db.execute.return_value = mock_cursor
        mock_get_db.return_value.__aenter__.return_value = mock_db

        result = await auth_svc.login_user("测试用户", "wrong_password")

        assert result is None

    def test_generate_user_id(self):
        """测试生成用户 UUID"""
        auth_svc = AuthService()
        user_id = auth_svc.generate_user_id()

        assert user_id is not None
        assert len(user_id) > 0
