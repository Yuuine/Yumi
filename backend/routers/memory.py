"""
Memory API Router
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ..core import get_logger

router = APIRouter()
logger = get_logger(__name__)


class MemoryItem(BaseModel):
    id: str
    content: str
    timestamp: str
    similarity: float
    decay_factor: float


class MemorySearchResult(BaseModel):
    memories: list[MemoryItem]
    total: int


class MemoryStats(BaseModel):
    total_memories: int
    oldest_memory: str | None
    newest_memory: str | None
    avg_importance: float


@router.get("/memory/search", response_model=MemorySearchResult)
async def search_memory(
    query: str,
    top_k: int = 6,
    decay_days: bool = True,
    req: Request = None
):
    memory_engine = req.app.state.memory_engine

    try:
        results = await memory_engine.search(
            query=query,
            top_k=top_k,
            apply_decay=decay_days
        )

        memories = [
            MemoryItem(
                id=item["id"],
                content=item["content"],
                timestamp=item["timestamp"],
                similarity=item["similarity"],
                decay_factor=item.get("decay_factor", 1.0)
            )
            for item in results
        ]

        return MemorySearchResult(
            memories=memories,
            total=len(memories)
        )

    except Exception as e:
        logger.error("Memory search error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="内存搜索失败，请稍后重试")


@router.get("/memory/stats", response_model=MemoryStats)
async def get_memory_stats(userId: str, req: Request):
    memory_engine = req.app.state.memory_engine

    try:
        stats = await memory_engine.get_stats(user_id=userId)
        return MemoryStats(**stats)

    except Exception as e:
        logger.error("Memory stats error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="获取内存统计失败，请稍后重试")
