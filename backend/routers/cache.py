"""
Cache API Router - 缓存监控接口
提供缓存统计、命中率查看等功能
"""

from __future__ import annotations

from fastapi import APIRouter

from ..core import get_logger
from ..services.cache_service import get_cache_service

router = APIRouter()
logger = get_logger(__name__)


@router.get("/cache/stats")
async def get_cache_stats():
    """获取所有缓存统计"""
    cache_service = get_cache_service()
    stats = cache_service.get_all_stats()
    return {"success": True, "data": stats}


@router.get("/cache/stats/{name}")
async def get_cache_stats_by_name(name: str):
    """获取指定缓存统计"""
    cache_service = get_cache_service()
    cache = cache_service.get_cache(name)
    if not cache:
        return {"success": False, "error": f"Cache '{name}' not found"}
    return {"success": True, "data": cache.get_stats().to_dict()}


@router.post("/cache/stats/reset")
async def reset_cache_stats():
    """重置所有缓存统计"""
    cache_service = get_cache_service()
    cache_service.reset_all_stats()
    logger.info("CacheRouter", "Stats reset")
    return {"success": True, "message": "Cache stats reset successfully"}


@router.post("/cache/stats/{name}/reset")
async def reset_cache_stats_by_name(name: str):
    """重置指定缓存统计"""
    cache_service = get_cache_service()
    cache = cache_service.get_cache(name)
    if not cache:
        return {"success": False, "error": f"Cache '{name}' not found"}
    cache.reset_stats()
    logger.info("CacheRouter", "Stats reset for", {"cache": name})
    return {"success": True, "message": f"Cache '{name}' stats reset successfully"}


@router.get("/cache/info")
async def get_cache_info():
    """获取缓存服务信息"""
    cache_service = get_cache_service()
    stats = cache_service.get_all_stats()

    total_hits = sum(s["hits"] for s in stats.values())
    total_misses = sum(s["misses"] for s in stats.values())
    total_requests = total_hits + total_misses
    overall_hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0

    return {
        "success": True,
        "data": {
            "total_hits": total_hits,
            "total_misses": total_misses,
            "total_requests": total_requests,
            "overall_hit_rate": round(overall_hit_rate, 2),
            "caches": list(stats.keys()),
        },
    }
