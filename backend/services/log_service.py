"""
Log Service - 统一日志记录服务
提供结构化日志记录，支持多种日志类型
基于 SQLModel 重构
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from ..core.logging import get_logger, request_id_var
from ..database_sqlmodel import get_log_session
from ..models import SystemLog, AuditLog

logger = get_logger(__name__)


class EventType(str, Enum):
    """日志事件类型"""

    USER_ACTION = "USER_ACTION"
    AI_INTERACTION = "AI_INTERACTION"
    API_CALL = "API_CALL"
    SYSTEM_EVENT = "SYSTEM_EVENT"
    SECURITY_AUDIT = "SECURITY_AUDIT"
    DB_OPERATION = "DB_OPERATION"


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
    USER_PROFILE_UPDATE = "USER_PROFILE_UPDATE"
    SETTINGS_UPDATE = "SETTINGS_UPDATE"
    MEMORY_STORE = "MEMORY_STORE"
    MEMORY_DELETE = "MEMORY_DELETE"
    MEMORY_CLEAR = "MEMORY_CLEAR"
    USER_REGISTER = "USER_REGISTER"
    USER_LOGIN = "USER_LOGIN"


class LogService:
    """统一日志服务"""

    @staticmethod
    def _get_trace_id() -> str | None:
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
        resource_id: str | None = None,
        result: str = "SUCCESS",
        user_id: str | None = None,
        session_id: str | None = None,
        duration_ms: float | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """记录用户操作日志"""
        trace_id = LogService._get_trace_id()
        timestamp = datetime.now(UTC)

        log_entry = {
            "timestamp": timestamp.isoformat(),
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
            async with get_log_session() as session:
                system_log = SystemLog(
                    timestamp=timestamp,
                    level="INFO",
                    event_type=EventType.USER_ACTION.value,
                    trace_id=trace_id,
                    user_id=user_id,
                    session_id=session_id,
                    content=json.dumps(log_entry, ensure_ascii=False),
                )
                session.add(system_log)
                await session.commit()
        except Exception as e:
            logger.error("Failed to save user action log: %s", e)

    @staticmethod
    async def log_ai_interaction(
        conversation_id: str | None,
        message_id: str | None,
        role: str,
        content: str,
        emotion: dict[str, Any] | None = None,
        model_info: dict[str, Any] | None = None,
        latency_ms: float | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> None:
        """记录 AI 交互日志"""
        trace_id = LogService._get_trace_id()
        timestamp = datetime.now(UTC)
        content_hash = LogService._generate_content_hash(content)

        log_entry = {
            "timestamp": timestamp.isoformat(),
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
            async with get_log_session() as session:
                system_log = SystemLog(
                    timestamp=timestamp,
                    level="INFO",
                    event_type=EventType.AI_INTERACTION.value,
                    trace_id=trace_id,
                    user_id=user_id,
                    session_id=session_id,
                    content=json.dumps(log_entry, ensure_ascii=False),
                )
                session.add(system_log)
                await session.commit()
        except Exception as e:
            logger.error("Failed to save AI interaction log: %s", e)

    @staticmethod
    async def log_api_call(
        provider: str,
        model: str,
        endpoint: str,
        status_code: int,
        latency_ms: float,
        request_tokens: int | None = None,
        response_tokens: int | None = None,
        error: str | None = None,
        retry_count: int = 0,
    ) -> None:
        """记录 API 调用日志"""
        trace_id = LogService._get_trace_id()
        timestamp = datetime.now(UTC)

        log_entry = {
            "timestamp": timestamp.isoformat(),
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
            async with get_log_session() as session:
                system_log = SystemLog(
                    timestamp=timestamp,
                    level="ERROR" if error else "INFO",
                    event_type=EventType.API_CALL.value,
                    trace_id=trace_id,
                    content=json.dumps(log_entry, ensure_ascii=False),
                )
                session.add(system_log)
                await session.commit()
        except Exception as e:
            logger.error("Failed to save API call log: %s", e)

    @staticmethod
    async def log_audit(
        action: AuditAction,
        resource_type: str,
        resource_id: str | None,
        result: str,
        user_id: str | None = None,
        client_ip: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """记录审计日志"""
        trace_id = LogService._get_trace_id()
        timestamp = datetime.now(UTC)

        log_entry = {
            "timestamp": timestamp.isoformat(),
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
            async with get_log_session() as session:
                audit_log = AuditLog(
                    timestamp=timestamp,
                    user_id=user_id,
                    action=action.value,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    result=result,
                    client_ip=client_ip,
                    details=details,
                )
                session.add(audit_log)
                await session.commit()
        except Exception as e:
            logger.error("Failed to save audit log: %s", e)

    @staticmethod
    async def log_db_operation(
        operation: str,
        table: str,
        resource_id: str | None = None,
        result: str = "SUCCESS",
        error: str | None = None,
        latency_ms: float | None = None,
        affected_rows: int | None = None,
        user_id: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """记录数据库操作日志

        Args:
            operation: 操作类型 (INSERT/UPDATE/DELETE)
            table: 表名
            resource_id: 资源ID
            result: 结果 (SUCCESS/FAIL)
            error: 错误信息
            latency_ms: 延迟毫秒数
            affected_rows: 影响行数
            user_id: 用户ID
            extra: 额外信息
        """
        trace_id = LogService._get_trace_id()
        timestamp = datetime.now(UTC)

        log_entry = {
            "timestamp": timestamp.isoformat(),
            "level": "ERROR" if error else "INFO",
            "event_type": EventType.DB_OPERATION.value,
            "trace_id": trace_id,
            "user_id": user_id,
            "operation": operation,
            "table": table,
            "resource_id": resource_id,
            "result": result,
            "error": error,
            "latency_ms": latency_ms,
            "affected_rows": affected_rows,
            "extra": extra or {},
        }

        if error:
            logger.error(
                "DB Operation FAILED: %s on %s - %s",
                operation,
                table,
                error,
                extra={"log_data": log_entry},
            )
        else:
            logger.info(
                "DB Operation: %s on %s.%s (%.2fms)",
                operation,
                table,
                f" id={resource_id}" if resource_id else "",
                latency_ms or 0,
                extra={"log_data": log_entry},
            )

        try:
            async with get_log_session() as session:
                system_log = SystemLog(
                    timestamp=timestamp,
                    level="ERROR" if error else "INFO",
                    event_type=EventType.DB_OPERATION.value,
                    trace_id=trace_id,
                    user_id=user_id,
                    content=json.dumps(log_entry, ensure_ascii=False),
                )
                session.add(system_log)
                await session.commit()
        except Exception as e:
            logger.error("Failed to save DB operation log: %s", e)


log_service = LogService()
