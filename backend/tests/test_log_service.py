"""
Tests for Log Service - 日志服务测试
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from services.log_service import LogService


class TestLogService:
    """测试日志服务"""

    def test_get_logs(self):
        """测试获取日志"""
        log_service = LogService()
        logs = log_service.get_logs(limit=10)
        assert isinstance(logs, list)

    def test_get_logs_with_type(self):
        """测试按类型获取日志"""
        log_service = LogService()
        logs = log_service.get_logs(log_type="system", limit=10)
        assert isinstance(logs, list)

    def test_get_logs_with_level(self):
        """测试按级别获取日志"""
        log_service = LogService()
        logs = log_service.get_logs(level="info", limit=10)
        assert isinstance(logs, list)

    def test_clear_logs(self):
        """测试清除日志"""
        log_service = LogService()
        result = log_service.clear_logs()
        assert isinstance(result, bool)
