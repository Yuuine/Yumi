"""
Database initialization and configuration with SQLModel
支持主数据库和日志数据库分离，使用 SQLModel ORM
基于新数据库设计重构
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
import logging

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlmodel import SQLModel, text, select
from sqlmodel.ext.asyncio.session import AsyncSession as SQLModelAsyncSession

# 延迟导入 settings 和 get_logger 以避免循环导入
logger = logging.getLogger(__name__)

# 模型导入
from .models import (
    User,
    CharacterCard,
    Conversation,
    ConversationLog,
    ModelProvider,
    ModelConfig,
    Setting,
    SystemLog,
    AuditLog,
    DialogueInteractionLog,
)

# 主数据库引擎
_main_engine = None
# 日志数据库引擎
_log_engine = None


def get_main_engine():
    """获取主数据库引擎"""
    global _main_engine
    if _main_engine is None:
        from .core import settings
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
        from .core import settings
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


async def init_model_providers(session: SQLModelAsyncSession) -> None:
    """初始化模型提供商数据"""
    providers = [
        ModelProvider(
            id="deepseek",
            name="deepseek",
            display_name="DeepSeek",
            description="DeepSeek AI - 高性能大语言模型"
        ),
        ModelProvider(
            id="kimi",
            name="kimi",
            display_name="Kimi",
            description="Moonshot AI - Kimi 系列模型"
        ),
        ModelProvider(
            id="custom",
            name="custom",
            display_name="自定义",
            description="自定义 API 提供商"
        ),
    ]

    for provider in providers:
        result = await session.exec(
            select(ModelProvider).where(ModelProvider.id == provider.id)
        )
        if not result.first():
            session.add(provider)
            logger.info(f"Inserted model provider: {provider.display_name}")


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
        # 初始化模型提供商
        await init_model_providers(session)
        await session.commit()

    from .core import settings
    logger.info("Main database initialized with SQLModel at %s", settings.database.full_path)


async def init_log_db() -> None:
    """初始化日志数据库 - 创建所有表"""
    engine = get_log_engine()

    # 使用 run_sync 来执行同步的 DDL 操作
    def create_tables(sync_conn):
        from sqlalchemy import MetaData

        # 创建日志表
        SystemLog.__table__.create(sync_conn, checkfirst=True)
        AuditLog.__table__.create(sync_conn, checkfirst=True)
        DialogueInteractionLog.__table__.create(sync_conn, checkfirst=True)

    async with engine.begin() as conn:
        await conn.run_sync(create_tables)

        # SQLite 优化设置
        await conn.execute(text("PRAGMA journal_mode=WAL"))
        await conn.execute(text("PRAGMA synchronous=NORMAL"))
        await conn.execute(text("PRAGMA cache_size=-64000"))
        await conn.execute(text("PRAGMA temp_store=MEMORY"))
        await conn.execute(text("PRAGMA mmap_size=268435456"))

    from .core import settings
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
