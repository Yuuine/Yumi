"""
Database initialization and configuration
支持主数据库和日志数据库分离
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import aiosqlite

from .core import get_logger, settings

logger = get_logger(__name__)


async def init_db() -> None:
    db_path = settings.database.full_path
    db_path.parent.mkdir(parents=True, exist_ok=True)

    db = await aiosqlite.connect(db_path)
    try:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA synchronous=NORMAL")
        await db.execute("PRAGMA cache_size=-64000")
        await db.execute("PRAGMA temp_store=MEMORY")
        await db.execute("PRAGMA mmap_size=268435456")

        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                role_name TEXT DEFAULT 'Yumi',
                preferences_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                character_id TEXT,
                title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (character_id) REFERENCES character_cards(id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS conversation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                emotion_valence REAL,
                emotion_arousal REAL,
                embedding_id TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS memory_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                conversation_id TEXT,
                summary TEXT NOT NULL,
                turn_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS model_providers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                display_name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS model_configs (
                id TEXT PRIMARY KEY,
                account_id TEXT NOT NULL DEFAULT '',
                provider_id TEXT NOT NULL,
                name TEXT NOT NULL,
                base_url TEXT NOT NULL,
                api_key TEXT,
                model_name TEXT NOT NULL,
                custom_model_name TEXT,
                model_type TEXT DEFAULT 'text',
                max_tokens INTEGER DEFAULT 4096,
                temperature REAL DEFAULT 0.85,
                is_enabled BOOLEAN DEFAULT 0,
                is_tested BOOLEAN DEFAULT 0,
                test_status TEXT DEFAULT 'untested',
                last_test_at TIMESTAMP,
                last_test_message TEXT,
                edit_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES users(id),
                FOREIGN KEY (provider_id) REFERENCES model_providers(id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                level TEXT NOT NULL,
                event_type TEXT NOT NULL,
                trace_id TEXT,
                user_id TEXT,
                session_id TEXT,
                content TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_id TEXT,
                action TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                resource_id TEXT,
                result TEXT NOT NULL,
                client_ip TEXT,
                details TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS character_cards (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                conversation_id TEXT,

                role_overview TEXT DEFAULT '',

                formal_name TEXT DEFAULT '',
                nickname TEXT DEFAULT '',
                race_or_form TEXT DEFAULT '人类',
                gender TEXT DEFAULT '中性',
                visual_age TEXT DEFAULT '',
                actual_age TEXT DEFAULT '',
                location TEXT DEFAULT '',
                appearance_desc TEXT DEFAULT '',

                core_personality TEXT DEFAULT '',
                self_perception TEXT DEFAULT '',
                attitude_to_user TEXT DEFAULT '',
                likes TEXT DEFAULT '',
                dislikes TEXT DEFAULT '',

                tone_base TEXT DEFAULT '',
                word_habits TEXT DEFAULT '',
                emotion_rules TEXT DEFAULT '',
                length_pref TEXT DEFAULT '',

                special_logic_list TEXT DEFAULT '',
                few_shot_examples TEXT DEFAULT '',

                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
        """)

        cursor = await db.execute("PRAGMA table_info(conversation_logs)")
        columns = [row[1] for row in await cursor.fetchall()]

        if "storage_status" not in columns:
            await db.execute(
                "ALTER TABLE conversation_logs ADD COLUMN storage_status TEXT DEFAULT 'pending'"
            )
            logger.info("Added storage_status column to conversation_logs")

        if "storage_attempts" not in columns:
            await db.execute(
                "ALTER TABLE conversation_logs ADD COLUMN storage_attempts INTEGER DEFAULT 0"
            )
            logger.info("Added storage_attempts column to conversation_logs")

        if "storage_error" not in columns:
            await db.execute("ALTER TABLE conversation_logs ADD COLUMN storage_error TEXT")
            logger.info("Added storage_error column to conversation_logs")

        if "stored_at" not in columns:
            await db.execute("ALTER TABLE conversation_logs ADD COLUMN stored_at TIMESTAMP")
            logger.info("Added stored_at column to conversation_logs")

        model_cursor = await db.execute("PRAGMA table_info(model_configs)")
        model_columns = [row[1] for row in await model_cursor.fetchall()]
        if "account_id" not in model_columns:
            await db.execute(
                "ALTER TABLE model_configs ADD COLUMN account_id TEXT NOT NULL DEFAULT ''"
            )
            await db.execute("DELETE FROM model_configs")
            logger.info("Added account_id column to model_configs and cleared legacy model records")

        conv_cursor = await db.execute("PRAGMA table_info(conversations)")
        conv_columns = [row[1] for row in await conv_cursor.fetchall()]
        if "character_id" not in conv_columns:
            await db.execute("ALTER TABLE conversations ADD COLUMN character_id TEXT")
            logger.info("Added character_id column to conversations")

        await _create_indexes(db)

        await db.execute("""
            INSERT OR IGNORE INTO users (id, role_name, preferences_json)
            VALUES ('default', 'Yumi',
                '{"communication_style": "warm", "topics_of_interest": ["生活", "工作", "情感"], "emotional_support_level": "high", "response_length": "medium"}'
            )
        """)

        await db.execute("""
            INSERT OR IGNORE INTO model_providers (id, name, display_name, description)
            VALUES
                ('deepseek', 'deepseek', 'DeepSeek', 'DeepSeek AI - 高性能大语言模型，支持深度思考模式'),
                ('kimi', 'kimi', 'Kimi', 'Moonshot AI - Kimi 系列模型，支持长文本和视觉理解'),
                ('custom', 'custom', '自定义', '自定义 API 提供商')
        """)

        await db.commit()
        logger.info("Main database initialized at %s", db_path)
    finally:
        await db.close()


async def init_log_db() -> None:
    log_db_path = settings.database.log_full_path
    log_db_path.parent.mkdir(parents=True, exist_ok=True)

    db = await aiosqlite.connect(log_db_path)
    try:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA synchronous=NORMAL")
        await db.execute("PRAGMA cache_size=-32000")

        await db.execute("""
            CREATE TABLE IF NOT EXISTS dialogue_interaction_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT,
                user_id TEXT NOT NULL,
                character_id TEXT,
                request_detail TEXT NOT NULL,
                response_detail TEXT,
                start_time TEXT NOT NULL,
                end_time TEXT,
                duration_ms INTEGER,
                is_normal_end INTEGER DEFAULT 1,
                end_reason TEXT DEFAULT '',
                user_emotion TEXT,
                assistant_emotion TEXT,
                trace_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await _create_log_indexes(db)

        await db.commit()
        logger.info("Log database initialized at %s", log_db_path)
    finally:
        await db.close()


async def _create_indexes(db: aiosqlite.Connection) -> None:
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_conversation_logs_user_time ON conversation_logs(user_id, timestamp DESC)",
        "CREATE INDEX IF NOT EXISTS idx_conversation_logs_conversation ON conversation_logs(conversation_id)",
        "CREATE INDEX IF NOT EXISTS idx_conversation_logs_storage_status ON conversation_logs(storage_status)",
        "CREATE INDEX IF NOT EXISTS idx_conversation_logs_storage_attempts ON conversation_logs(storage_attempts)",
        "CREATE INDEX IF NOT EXISTS idx_conversation_logs_stored_at ON conversation_logs(stored_at)",
        "CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_conversations_active ON conversations(user_id, is_active)",
        "CREATE INDEX IF NOT EXISTS idx_conversations_character ON conversations(character_id)",
        "CREATE INDEX IF NOT EXISTS idx_memory_summaries_user ON memory_summaries(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_model_configs_provider ON model_configs(provider_id)",
        "CREATE INDEX IF NOT EXISTS idx_model_configs_account ON model_configs(account_id)",
        "CREATE INDEX IF NOT EXISTS idx_model_configs_account_enabled ON model_configs(account_id, is_enabled)",
        "CREATE INDEX IF NOT EXISTS idx_model_configs_enabled ON model_configs(is_enabled)",
        "CREATE INDEX IF NOT EXISTS idx_model_configs_type ON model_configs(model_type)",
        "CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs(timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(level)",
        "CREATE INDEX IF NOT EXISTS idx_system_logs_event_type ON system_logs(event_type)",
        "CREATE INDEX IF NOT EXISTS idx_system_logs_trace_id ON system_logs(trace_id)",
        "CREATE INDEX IF NOT EXISTS idx_system_logs_user_id ON system_logs(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action)",
        "CREATE INDEX IF NOT EXISTS idx_character_cards_user ON character_cards(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_character_cards_conversation ON character_cards(conversation_id)",
    ]

    for index_sql in indexes:
        await db.execute(index_sql)


async def _create_log_indexes(db: aiosqlite.Connection) -> None:
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_dialogue_logs_user_time ON dialogue_interaction_logs(user_id, start_time DESC)",
        "CREATE INDEX IF NOT EXISTS idx_dialogue_logs_conversation ON dialogue_interaction_logs(conversation_id)",
        "CREATE INDEX IF NOT EXISTS idx_dialogue_logs_character ON dialogue_interaction_logs(character_id)",
        "CREATE INDEX IF NOT EXISTS idx_dialogue_logs_status ON dialogue_interaction_logs(is_normal_end)",
        "CREATE INDEX IF NOT EXISTS idx_dialogue_logs_start_time ON dialogue_interaction_logs(start_time)",
        "CREATE INDEX IF NOT EXISTS idx_dialogue_logs_trace_id ON dialogue_interaction_logs(trace_id)",
    ]

    for index_sql in indexes:
        await db.execute(index_sql)


@asynccontextmanager
async def get_db() -> AsyncIterator[aiosqlite.Connection]:
    """获取主数据库连接的上下文管理器

    Usage:
        async with get_db() as db:
            await db.execute(...)
            await db.commit()
    """
    db = await aiosqlite.connect(settings.database.full_path)
    try:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA synchronous=NORMAL")
        yield db
    finally:
        await db.close()


@asynccontextmanager
async def get_log_db() -> AsyncIterator[aiosqlite.Connection]:
    """获取日志数据库连接的上下文管理器

    Usage:
        async with get_log_db() as db:
            await db.execute(...)
            await db.commit()
    """
    db = await aiosqlite.connect(settings.database.log_full_path)
    try:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA synchronous=NORMAL")
        yield db
    finally:
        await db.close()
