"""
Database initialization and configuration with SQLModel
支持主数据库和日志数据库分离，使用 SQLModel ORM
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlmodel import SQLModel, text, select
from sqlmodel.ext.asyncio.session import AsyncSession as SQLModelAsyncSession

from .core import get_logger, settings
from .models import (
    User,
)

logger = get_logger(__name__)

# 主数据库引擎
_main_engine = None
# 日志数据库引擎
_log_engine = None


def get_main_engine():
    """获取主数据库引擎"""
    global _main_engine
    if _main_engine is None:
        db_path = settings.database.full_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        database_url = f"sqlite+aiosqlite:///{db_path}"
        _main_engine = create_async_engine(
            database_url,
            echo=settings.app.debug,
            future=True
        )
    return _main_engine


def get_log_engine():
    """获取日志数据库引擎"""
    global _log_engine
    if _log_engine is None:
        db_path = settings.database.log_full_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        database_url = f"sqlite+aiosqlite:///{db_path}"
        _log_engine = create_async_engine(
            database_url,
            echo=settings.app.debug,
            future=True
        )
    return _log_engine


@asynccontextmanager
async def get_session() -> AsyncIterator[SQLModelAsyncSession]:
    """
    获取主数据库会话的上下文管理器

    Usage:
        async with get_session() as session:
            result = await session.exec(select(User))
            users = result.all()
    """
    engine = get_main_engine()
    async with SQLModelAsyncSession(engine, expire_on_commit=False) as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_log_session() -> AsyncIterator[SQLModelAsyncSession]:
    """
    获取日志数据库会话的上下文管理器

    Usage:
        async with get_log_session() as session:
            await session.add(system_log)
            await session.commit()
    """
    engine = get_log_engine()
    async with SQLModelAsyncSession(engine, expire_on_commit=False) as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """初始化主数据库 - 创建所有表和初始数据"""
    engine = get_main_engine()

    async with engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(SQLModel.metadata.create_all)

        # SQLite 优化设置
        await conn.execute(text("PRAGMA journal_mode=WAL"))
        await conn.execute(text("PRAGMA synchronous=NORMAL"))
        await conn.execute(text("PRAGMA cache_size=-64000"))
        await conn.execute(text("PRAGMA temp_store=MEMORY"))
        await conn.execute(text("PRAGMA mmap_size=268435456"))

    # 插入初始数据
    async with get_session() as session:
        # 检查是否已有默认用户
        result = await session.exec(select(User).where(User.id == "default"))
        default_user = result.first()

        if not default_user:
            default_user = User(
                id="default",
                role_name="Yumi",
                preferences_json='{"communication_style": "warm", "topics_of_interest": ["生活", "工作", "情感"], "emotional_support_level": "high", "response_length": "medium"}'
            )
            session.add(default_user)
            await session.commit()
            logger.info("Inserted default user")

    logger.info("Main database initialized with SQLModel at %s", settings.database.full_path)


async def init_log_db() -> None:
    """初始化日志数据库 - 创建所有表"""
    logger.info("Log database initialized with SQLModel at %s", settings.database.log_full_path)


async def close_engines():
    """关闭所有数据库引擎"""
    global _main_engine, _log_engine

    if _main_engine:
        await _main_engine.dispose()
        _main_engine = None

    if _log_engine:
        await _log_engine.dispose()
        _log_engine = None
