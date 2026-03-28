"""
SQLModel Database Models - 数据库模型
"""

from .user import User, UserCreate, UserUpdate, UserResponse
from .character_card import CharacterCard, CharacterCardCreate, CharacterCardUpdate
from .conversation import Conversation, ConversationCreate, ConversationUpdate, ConversationResponse
from .conversation_log import ConversationLog, ConversationLogCreate, ConversationLogResponse
from .model_provider import ModelProvider, ModelProviderCreate, ModelProviderUpdate
from .model_config import ModelConfig, ModelConfigCreate, ModelConfigUpdate
from .setting import Setting, SettingCreate, SettingUpdate
from .system_log import SystemLog, SystemLogCreate
from .audit_log import AuditLog, AuditLogCreate
from .dialogue_interaction_log import DialogueInteractionLog, DialogueInteractionLogCreate

__all__ = [
    # 用户模型
    "User",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    # 角色卡模型
    "CharacterCard",
    "CharacterCardCreate",
    "CharacterCardUpdate",
    # 对话模型
    "Conversation",
    "ConversationCreate",
    "ConversationUpdate",
    "ConversationResponse",
    # 对话消息模型
    "ConversationLog",
    "ConversationLogCreate",
    "ConversationLogResponse",
    # 模型提供商
    "ModelProvider",
    "ModelProviderCreate",
    "ModelProviderUpdate",
    # 模型配置
    "ModelConfig",
    "ModelConfigCreate",
    "ModelConfigUpdate",
    # 系统设置
    "Setting",
    "SettingCreate",
    "SettingUpdate",
    # 日志模型
    "SystemLog",
    "SystemLogCreate",
    "AuditLog",
    "AuditLogCreate",
    "DialogueInteractionLog",
    "DialogueInteractionLogCreate",
]
