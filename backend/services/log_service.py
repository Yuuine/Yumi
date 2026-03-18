"""
Log Service - 统一日志记录服务
提供结构化日志记录，支持多种日志类型
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from ..core.logging import get_logger, request_id_var
from ..database import get_db

logger = get_logger(__name__)


class EventType(str, Enum):
    """日志事件类型"""
    USER_ACTION = "USER_ACTION"
    AI_INTERACTION = "AI_INTERACTION"
    API_CALL = "API_CALL"
    SYSTEM_EVENT = "SYSTEM_EVENT"
    SECURITY_AUDIT = "SECURITY_AUDIT"


class AuditAction(str, Enum):
    """审计动作类型"""
    MODEL_KEY_ADD = "MODEL_KEY_ADD"
    MODEL_KEY_UPDATE = "MODEL_KEY_UPDATE"
    MODEL_KEY_DELETE = "MODEL_KEY_DELETE"
    MODEL_ENABLE = "MODEL_ENABLE"
    MODEL_DISABLE = "MODEL_DISABLE"
    SETTINGS_CHANGE = "SETTINGS_CHANGE"
    DATA_EXPORT = "DATA_EXPORT"
    DATA_DELETE = "DATA_DELETE"


class LogService:
    """统一日志服务"""

    @staticmethod
    def _get_trace_id() -> Optional[str]:
        """获取当前请求的 trace_id"""
        try:
            return request_id_var.get()
        except LookupError:
            return None

    @staticmethod
    def _generate_content_hash(content: str) -> str:
        """生成内容哈希"""
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    @staticmethod
    async def log_user_action(
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        result: str = "SUCCESS",
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        duration_ms: Optional[float] = None,
        extra: Optional[dict[str, Any]] = None,
    ) -> None:
        """记录用户操作日志"""
        trace_id = LogService._get_trace_id()
        timestamp = datetime.utcnow().isoformat()

        log_entry = {
            "timestamp": timestamp,
            "level": "INFO",
            "event_type": EventType.USER_ACTION.value,
            "trace_id": trace_id,
            "user_id": user_id,
            "session_id": session_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "result": result,
            "duration_ms": duration_ms,
            "extra": extra or {},
        }

        logger.info(
            "User action: %s on %s%s",
            action,
            resource_type,
            f" ({result})" if result != "SUCCESS" else "",
            extra={"log_data": log_entry},
        )

        try:
            async with get_db() as db:
                await db.execute(
                    """INSERT INTO system_logs 
                       (timestamp, level, event_type, trace_id, user_id, session_id, content)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        timestamp,
                        "INFO",
                        EventType.USER_ACTION.value,
                        trace_id,
                        user_id,
                        session_id,
                        json.dumps(log_entry, ensure_ascii=False),
                    ),
                )
                await db.commit()
        except Exception as e:
            logger.error("Failed to save user action log: %s", e)

    @staticmethod
    async def log_ai_interaction(
        conversation_id: Optional[str],
        message_id: Optional[str],
        role: str,
        content: str,
        emotion: Optional[dict[str, Any]] = None,
        model_info: Optional[dict[str, Any]] = None,
        latency_ms: Optional[float] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> None:
        """记录 AI 交互日志"""
        trace_id = LogService._get_trace_id()
        timestamp = datetime.utcnow().isoformat()
        content_hash = LogService._generate_content_hash(content)

        log_entry = {
            "timestamp": timestamp,
            "level": "INFO",
            "event_type": EventType.AI_INTERACTION.value,
            "trace_id": trace_id,
            "user_id": user_id,
            "session_id": session_id,
            "conversation_id": conversation_id,
            "message_id": message_id,
            "role": role,
            "content_hash": content_hash,
            "content_length": len(content),
            "emotion": emotion,
            "model_info": model_info,
            "latency_ms": latency_ms,
        }

        logger.info(
            "AI interaction: %s message in conversation %s",
            role,
            conversation_id or "new",
            extra={"log_data": log_entry},
        )

        try:
            async with get_db() as db:
                await db.execute(
                    """INSERT INTO system_logs 
                       (timestamp, level, event_type, trace_id, user_id, session_id, content)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        timestamp,
                        "INFO",
                        EventType.AI_INTERACTION.value,
                        trace_id,
                        user_id,
                        session_id,
                        json.dumps(log_entry, ensure_ascii=False),
                    ),
                )
                await db.commit()
        except Exception as e:
            logger.error("Failed to save AI interaction log: %s", e)

    @staticmethod
    async def log_api_call(
        provider: str,
        model: str,
        endpoint: str,
        status_code: int,
        latency_ms: float,
        request_tokens: Optional[int] = None,
        response_tokens: Optional[int] = None,
        error: Optional[str] = None,
        retry_count: int = 0,
    ) -> None:
        """记录 API 调用日志"""
        trace_id = LogService._get_trace_id()
        timestamp = datetime.utcnow().isoformat()

        log_entry = {
            "timestamp": timestamp,
            "level": "ERROR" if error else "INFO",
            "event_type": EventType.API_CALL.value,
            "trace_id": trace_id,
            "provider": provider,
            "model": model,
            "endpoint": endpoint,
            "status_code": status_code,
            "latency_ms": latency_ms,
            "request_tokens": request_tokens,
            "response_tokens": response_tokens,
            "error": error,
            "retry_count": retry_count,
        }

        if error:
            logger.error(
                "API call failed: %s/%s - %s",
                provider,
                model,
                error,
                extra={"log_data": log_entry},
            )
        else:
            logger.info(
                "API call: %s/%s (%.2fms)",
                provider,
                model,
                latency_ms,
                extra={"log_data": log_entry},
            )

        try:
            async with get_db() as db:
                await db.execute(
                    """INSERT INTO system_logs 
                       (timestamp, level, event_type, trace_id, content)
                       VALUES (?, ?, ?, ?, ?)""",
                    (
                        timestamp,
                        log_entry["level"],
                        EventType.API_CALL.value,
                        trace_id,
                        json.dumps(log_entry, ensure_ascii=False),
                    ),
                )
                await db.commit()
        except Exception as e:
            logger.error("Failed to save API call log: %s", e)

    @staticmethod
    async def log_audit(
        action: AuditAction,
        resource_type: str,
        resource_id: Optional[str],
        result: str,
        user_id: Optional[str] = None,
        client_ip: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """记录审计日志"""
        trace_id = LogService._get_trace_id()
        timestamp = datetime.utcnow().isoformat()

        log_entry = {
            "timestamp": timestamp,
            "level": "INFO",
            "event_type": EventType.SECURITY_AUDIT.value,
            "trace_id": trace_id,
            "user_id": user_id,
            "action": action.value,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "result": result,
            "client_ip": client_ip,
            "details": details,
        }

        logger.info(
            "Audit: %s on %s (%s)",
            action.value,
            resource_type,
            result,
            extra={"log_data": log_entry},
        )

        try:
            async with get_db() as db:
                await db.execute(
                    """INSERT INTO audit_logs 
                       (timestamp, user_id, action, resource_type, resource_id, result, client_ip, details)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        timestamp,
                        user_id,
                        action.value,
                        resource_type,
                        resource_id,
                        result,
                        client_ip,
                        json.dumps(details, ensure_ascii=False) if details else None,
                    ),
                )
                await db.commit()
        except Exception as e:
            logger.error("Failed to save audit log: %s", e)


log_service = LogService()
