"""
Log Query API Router - 日志查询接口
基于 SQLModel 重构
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from io import BytesIO
from typing import Any

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlmodel import select, func

from ..core import get_logger
from ..database_sqlmodel import get_log_session
from ..models import SystemLog, AuditLog

router = APIRouter()
logger = get_logger(__name__)

EXPORT_SENSITIVE_PATTERNS = [
    (
        re.compile(
            r"(api[_-]?key|apikey|token|secret|password|pwd)['\"]?\s*[:=]\s*['\"]?([^'\"\\s,}]+)",
            re.IGNORECASE,
        ),
        r"\1=***REDACTED***",
    ),
    (re.compile(r"(Bearer\s+)[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE), r"\1***REDACTED***"),
    (re.compile(r"(sk-[a-zA-Z0-9]{20,})"), r"sk-***REDACTED***"),
    (re.compile(r"(kimi-[a-zA-Z0-9]{20,})"), r"kimi-***REDACTED***"),
]


def sanitize_content(content: str) -> str:
    """脱敏日志内容"""
    result = content
    for pattern, replacement in EXPORT_SENSITIVE_PATTERNS:
        result = pattern.sub(replacement, result)
    return result


class LogEntry(BaseModel):
    id: int
    timestamp: str
    level: str
    event_type: str
    trace_id: str | None = None
    user_id: str | None = None
    session_id: str | None = None
    content: str


class AuditLogEntry(BaseModel):
    id: int
    timestamp: str
    user_id: str | None = None
    action: str
    resource_type: str
    resource_id: str | None = None
    result: str
    client_ip: str | None = None
    details: dict | None = None


class LogQueryResponse(BaseModel):
    total: int
    items: list[LogEntry]
    aggregations: dict | None = None


class AuditLogQueryResponse(BaseModel):
    total: int
    items: list[AuditLogEntry]


class LogStatsResponse(BaseModel):
    total_logs: int
    logs_by_level: dict[str, int]
    logs_by_event_type: dict[str, int]
    logs_last_24h: int
    logs_last_7d: int


@router.get("/logs", response_model=LogQueryResponse)
async def query_logs(
    start_time: str | None = Query(None, description="开始时间 (ISO8601)"),
    end_time: str | None = Query(None, description="结束时间 (ISO8601)"),
    level: str | None = Query(None, description="日志级别"),
    event_type: str | None = Query(None, description="事件类型"),
    trace_id: str | None = Query(None, description="追踪ID"),
    user_id: str | None = Query(None, description="用户ID"),
    keyword: str | None = Query(None, description="关键词搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
):
    """查询系统日志"""
    offset = (page - 1) * page_size

    try:
        async with get_log_session() as session:
            # 构建查询条件
            query = select(SystemLog)

            if start_time:
                query = query.where(SystemLog.timestamp >= start_time)
            if end_time:
                query = query.where(SystemLog.timestamp <= end_time)
            if level:
                query = query.where(SystemLog.level == level.upper())
            if event_type:
                query = query.where(SystemLog.event_type == event_type.upper())
            if trace_id:
                query = query.where(SystemLog.trace_id == trace_id)
            if user_id:
                query = query.where(SystemLog.user_id == user_id)
            if keyword:
                query = query.where(SystemLog.content.contains(keyword))

            # 获取总数
            count_result = await session.exec(select(func.count()).select_from(query.subquery()))
            total = count_result.one()

            # 获取分页数据
            query = query.order_by(SystemLog.timestamp.desc()).offset(offset).limit(page_size)
            result = await session.exec(query)
            logs = result.all()

            items = [
                LogEntry(
                    id=log.id,
                    timestamp=log.timestamp.isoformat() if log.timestamp else "",
                    level=log.level,
                    event_type=log.event_type,
                    trace_id=log.trace_id,
                    user_id=log.user_id,
                    session_id=log.session_id,
                    content=log.content,
                )
                for log in logs
            ]

            # 聚合统计
            aggregations = None
            if page == 1:
                level_query = select(SystemLog.level, func.count()).group_by(SystemLog.level)
                if start_time:
                    level_query = level_query.where(SystemLog.timestamp >= start_time)
                if end_time:
                    level_query = level_query.where(SystemLog.timestamp <= end_time)
                level_result = await session.exec(level_query)
                logs_by_level = {row[0]: row[1] for row in level_result.all()}

                type_query = select(SystemLog.event_type, func.count()).group_by(SystemLog.event_type)
                if start_time:
                    type_query = type_query.where(SystemLog.timestamp >= start_time)
                if end_time:
                    type_query = type_query.where(SystemLog.timestamp <= end_time)
                type_result = await session.exec(type_query)
                logs_by_type = {row[0]: row[1] for row in type_result.all()}

                aggregations = {
                    "byLevel": logs_by_level,
                    "byEventType": logs_by_type,
                }

            return LogQueryResponse(
                total=total,
                items=items,
                aggregations=aggregations,
            )

    except Exception as e:
        logger.error("Failed to query logs: %s", e)
        return LogQueryResponse(total=0, items=[])


@router.get("/logs/audit", response_model=AuditLogQueryResponse)
async def query_audit_logs(
    start_time: str | None = Query(None, description="开始时间 (ISO8601)"),
    end_time: str | None = Query(None, description="结束时间 (ISO8601)"),
    user_id: str | None = Query(None, description="用户ID"),
    action: str | None = Query(None, description="操作类型"),
    resource_type: str | None = Query(None, description="资源类型"),
    result: str | None = Query(None, description="结果"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
):
    """查询审计日志"""
    offset = (page - 1) * page_size

    try:
        async with get_log_session() as session:
            # 构建查询条件
            query = select(AuditLog)

            if start_time:
                query = query.where(AuditLog.timestamp >= start_time)
            if end_time:
                query = query.where(AuditLog.timestamp <= end_time)
            if user_id:
                query = query.where(AuditLog.user_id == user_id)
            if action:
                query = query.where(AuditLog.action == action.upper())
            if resource_type:
                query = query.where(AuditLog.resource_type == resource_type.lower())
            if result:
                query = query.where(AuditLog.result == result.upper())

            # 获取总数
            count_result = await session.exec(select(func.count()).select_from(query.subquery()))
            total = count_result.one()

            # 获取分页数据
            query = query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(page_size)
            result_query = await session.exec(query)
            logs = result_query.all()

            items = [
                AuditLogEntry(
                    id=log.id,
                    timestamp=log.timestamp.isoformat() if log.timestamp else "",
                    user_id=log.user_id,
                    action=log.action,
                    resource_type=log.resource_type,
                    resource_id=log.resource_id,
                    result=log.result,
                    client_ip=log.client_ip,
                    details=log.details,
                )
                for log in logs
            ]

            return AuditLogQueryResponse(total=total, items=items)

    except Exception as e:
        logger.error("Failed to query audit logs: %s", e)
        return AuditLogQueryResponse(total=0, items=[])


@router.get("/logs/stats", response_model=LogStatsResponse)
async def get_log_stats():
    """获取日志统计信息"""
    try:
        async with get_log_session() as session:
            # 总数
            count_result = await session.exec(select(func.count(SystemLog.id)))
            total_logs = count_result.one()

            # 按级别统计
            level_query = select(SystemLog.level, func.count()).group_by(SystemLog.level)
            level_result = await session.exec(level_query)
            logs_by_level = {row[0]: row[1] for row in level_result.all()}

            # 按事件类型统计
            type_query = select(SystemLog.event_type, func.count()).group_by(SystemLog.event_type)
            type_result = await session.exec(type_query)
            logs_by_event_type = {row[0]: row[1] for row in type_result.all()}

            # 最近24小时
            now = datetime.now(timezone.utc)
            last_24h = (now - timedelta(hours=24)).isoformat()
            last_7d = (now - timedelta(days=7)).isoformat()

            count_24h = await session.exec(
                select(func.count(SystemLog.id)).where(SystemLog.timestamp >= last_24h)
            )
            logs_last_24h = count_24h.one()

            count_7d = await session.exec(
                select(func.count(SystemLog.id)).where(SystemLog.timestamp >= last_7d)
            )
            logs_last_7d = count_7d.one()

            return LogStatsResponse(
                total_logs=total_logs,
                logs_by_level=logs_by_level,
                logs_by_event_type=logs_by_event_type,
                logs_last_24h=logs_last_24h,
                logs_last_7d=logs_last_7d,
            )

    except Exception as e:
        logger.error("Failed to get log stats: %s", e)
        return LogStatsResponse(
            total_logs=0,
            logs_by_level={},
            logs_by_event_type={},
            logs_last_24h=0,
            logs_last_7d=0,
        )


@router.get("/logs/export")
async def export_logs(
    start_time: str | None = Query(None, description="开始时间 (ISO8601)"),
    end_time: str | None = Query(None, description="结束时间 (ISO8601)"),
    level: str | None = Query(None, description="日志级别"),
    event_type: str | None = Query(None, description="事件类型"),
    sanitize: bool = Query(True, description="是否脱敏处理"),
):
    """导出日志文件"""
    try:
        async with get_log_session() as session:
            # 构建查询条件
            query = select(SystemLog)

            if start_time:
                query = query.where(SystemLog.timestamp >= start_time)
            if end_time:
                query = query.where(SystemLog.timestamp <= end_time)
            if level:
                query = query.where(SystemLog.level == level.upper())
            if event_type:
                query = query.where(SystemLog.event_type == event_type.upper())

            # 获取数据（限制10000条）
            query = query.order_by(SystemLog.timestamp.desc()).limit(10000)
            result = await session.exec(query)
            logs = result.all()

            export_data = {
                "export_time": datetime.now(timezone.utc).isoformat(),
                "total_count": len(logs),
                "sanitized": sanitize,
                "logs": [
                    {
                        "id": log.id,
                        "timestamp": log.timestamp.isoformat() if log.timestamp else "",
                        "level": log.level,
                        "event_type": log.event_type,
                        "trace_id": log.trace_id,
                        "user_id": log.user_id,
                        "session_id": log.session_id,
                        "content": sanitize_content(log.content) if sanitize else log.content,
                    }
                    for log in logs
                ],
            }

            json_content = json.dumps(export_data, ensure_ascii=False, indent=2)
            buffer = BytesIO(json_content.encode("utf-8"))

            filename = f"yumi_logs_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"

            return StreamingResponse(
                buffer,
                media_type="application/json",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"',
                },
            )

    except Exception as e:
        logger.error("Failed to export logs: %s", e)
        raise


@router.get("/logs/audit/export")
async def export_audit_logs(
    start_time: str | None = Query(None, description="开始时间 (ISO8601)"),
    end_time: str | None = Query(None, description="结束时间 (ISO8601)"),
    action: str | None = Query(None, description="操作类型"),
    sanitize: bool = Query(True, description="是否脱敏处理"),
):
    """导出审计日志文件"""
    try:
        async with get_log_session() as session:
            # 构建查询条件
            query = select(AuditLog)

            if start_time:
                query = query.where(AuditLog.timestamp >= start_time)
            if end_time:
                query = query.where(AuditLog.timestamp <= end_time)
            if action:
                query = query.where(AuditLog.action == action.upper())

            # 获取数据（限制10000条）
            query = query.order_by(AuditLog.timestamp.desc()).limit(10000)
            result = await session.exec(query)
            logs = result.all()

            export_logs_data = []
            for log in logs:
                details = log.details
                if sanitize and details:
                    details_str = json.dumps(details, ensure_ascii=False)
                    details_str = sanitize_content(details_str)
                    details = json.loads(details_str)

                export_logs_data.append({
                    "id": log.id,
                    "timestamp": log.timestamp.isoformat() if log.timestamp else "",
                    "user_id": log.user_id,
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "result": log.result,
                    "client_ip": log.client_ip,
                    "details": details,
                })

            export_data = {
                "export_time": datetime.now(timezone.utc).isoformat(),
                "total_count": len(export_logs_data),
                "sanitized": sanitize,
                "audit_logs": export_logs_data,
            }

            json_content = json.dumps(export_data, ensure_ascii=False, indent=2)
            buffer = BytesIO(json_content.encode("utf-8"))

            filename = f"yumi_audit_logs_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"

            return StreamingResponse(
                buffer,
                media_type="application/json",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"',
                },
            )

    except Exception as e:
        logger.error("Failed to export audit logs: %s", e)
        raise
