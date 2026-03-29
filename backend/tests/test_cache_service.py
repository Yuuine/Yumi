"""
Tests for Cache Service - 缓存服务测试
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from services.cache_service import CacheService


class TestCacheService:
    """测试缓存服务"""

    def test_set_and_get(self):
        """测试设置和获取缓存"""
        cache = CacheService()
        cache.set("test_key", "test_value", ttl=60)
        value = cache.get("test_key")
        assert value == "test_value"

    def test_get_nonexistent(self):
        """测试获取不存在的键"""
        cache = CacheService()
        value = cache.get("nonexistent_key")
        assert value is None

    def test_delete(self):
        """测试删除缓存"""
        cache = CacheService()
        cache.set("delete_test", "value")
        cache.delete("delete_test")
        value = cache.get("delete_test")
        assert value is None

    def test_clear(self):
        """测试清除所有缓存"""
        cache = CacheService()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_exists(self):
        """测试检查键是否存在"""
        cache = CacheService()
        cache.set("exists_test", "value")
        assert cache.exists("exists_test") is True
        assert cache.exists("nonexistent") is False
