"""
配置管理模块
使用 pydantic-settings 实现类型安全的配置管理
支持环境变量覆盖和 YAML 配置文件
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="YUMI_")

    name: str = "Yumi"
    version: str = "1.0.0"
    debug: bool = False


class ServerConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="YUMI_SERVER_")

    host: str = "127.0.0.1"
    port: int = 8000
    cors_origins: list[str] = Field(
        default=["http://localhost:1420", "http://127.0.0.1:1420", "tauri://localhost"]
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",")]
        return value


class DatabaseConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="YUMI_DB_")

    type: str = "sqlite"
    path: str = "data/yumi.db"
    log_path: str = "data/yumi_logs.db"

    @property
    def full_path(self) -> Path:
        return Path(self.path).resolve()

    @property
    def log_full_path(self) -> Path:
        return Path(self.log_path).resolve()


class VectorDBConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="YUMI_VECTOR_")

    type: str = "chromadb"
    persist_dir: str = "data/chroma"
    collection_name: str = "echo_memory"

    @property
    def full_path(self) -> Path:
        return Path(self.persist_dir).resolve()


class LLMConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="YUMI_LLM_", protected_namespaces=())

    api_endpoint: str = "http://127.0.0.1:11434/v1"
    api_key: str = ""
    model_name: str = "llama3.1:8b"
    max_tokens: int = 4096
    default_temperature: float = 0.85
    timeout: int = 60


class MemoryConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="YUMI_MEMORY_")

    recent_context_limit: int = 20
    rag_top_k: int = 6
    summary_trigger_turns: int = 70
    summary_context_size: int = 35
    decay_rate: float = 0.03
    min_decay_factor: float = 0.1
    deduplication_threshold: float = 0.85
    consolidation_boost: float = 0.1


class EmotionConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="YUMI_EMOTION_")

    detection_enabled: bool = True
    model: str = "keyword"
    ai_emotion_enabled: bool = True
    empathy_factor: float = Field(default=0.3, ge=0.0, le=1.0)
    emotion_half_life: int = Field(default=1800, ge=1, description="AI 情绪半衰期（秒）")
    default_base_valence: float = Field(default=0.3, ge=-1.0, le=1.0)
    default_base_arousal: float = Field(default=0.4, ge=0.0, le=1.0)
    default_sensitivity: float = Field(default=0.7, ge=0.0, le=1.0)


class LoggingConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="YUMI_LOG_")

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    dir: str = "logs"
    enable_file: bool = True
    enable_json: bool = False
    max_file_size_mb: int = 10
    backup_count: int = 5
    retention_days: int = 30


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="YUMI_")

    app: AppConfig = Field(default_factory=AppConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    vector_db: VectorDBConfig = Field(default_factory=VectorDBConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    emotion: EmotionConfig = Field(default_factory=EmotionConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    @classmethod
    def from_yaml(cls, config_path: str | Path) -> Settings:
        config_path = Path(config_path)
        if not config_path.exists():
            return cls()

        with open(config_path, encoding="utf-8") as file:
            config_data = yaml.safe_load(file)

        return cls.model_validate(config_data or {})


CONFIG_FILE_PATH = Path(__file__).parent.parent.parent / "config.yaml"


@lru_cache
def get_settings() -> Settings:
    return Settings.from_yaml(CONFIG_FILE_PATH)


settings = get_settings()
