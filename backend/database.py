"""
Database initialization and configuration
"""
from __future__ import annotations

import logging

import aiosqlite

from .core import settings

logger = logging.getLogger(__name__)


async def init_db() -> None:
    db_path = settings.database.full_path
    db_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                role_name TEXT DEFAULT 'Yumi',
                big_five_json TEXT,
                preferences_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id)
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

        await _create_indexes(db)

        await db.execute("""
            INSERT OR IGNORE INTO users (id, role_name, big_five_json, preferences_json)
            VALUES ('default', 'Yumi', 
                '{"openness": 0.75, "conscientiousness": 0.70, "extraversion": 0.65, "agreeableness": 0.80, "neuroticism": 0.35}',
                '{"communication_style": "warm", "topics_of_interest": ["生活", "工作", "情感"], "emotional_support_level": "high", "response_length": "medium"}'
            )
        """)

        await db.commit()
        logger.info("Database initialized at %s", db_path)


async def _create_indexes(db: aiosqlite.Connection) -> None:
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_conversation_logs_user_time ON conversation_logs(user_id, timestamp DESC)",
        "CREATE INDEX IF NOT EXISTS idx_conversation_logs_conversation ON conversation_logs(conversation_id)",
        "CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_conversations_active ON conversations(user_id, is_active)",
        "CREATE INDEX IF NOT EXISTS idx_memory_summaries_user ON memory_summaries(user_id)",
    ]

    for index_sql in indexes:
        await db.execute(index_sql)


async def get_db() -> aiosqlite.Connection:
    return aiosqlite.connect(settings.database.full_path)
