"""
Log Query API Router - 日志查询接口
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from io import BytesIO
from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..core import get_logger
from ..database import get_db

router = APIRouter()
logger = get_logger(__name__)

EXPORT_SENSITIVE_PATTERNS = [
    (re.compile(r"(api[_-]?key|apikey|token|secret|password|pwd)['\"]?\s*[:=]\s*['\"]?([^'\"\\s,}]+)", re.IGNORECASE), r"\1=***REDACTED***"),
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
    trace_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    content: str


class AuditLogEntry(BaseModel):
    id: int
    timestamp: str
    user_id: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    result: str
    client_ip: Optional[str] = None
    details: Optional[dict] = None


class LogQueryResponse(BaseModel):
    total: int
    items: list[LogEntry]
    aggregations: Optional[dict] = None


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
    start_time: Optional[str] = Query(None, description="开始时间 (ISO8601)"),
    end_time: Optional[str] = Query(None, description="结束时间 (ISO8601)"),
    level: Optional[str] = Query(None, description="日志级别"),
    event_type: Optional[str] = Query(None, description="事件类型"),
    trace_id: Optional[str] = Query(None, description="追踪ID"),
    user_id: Optional[str] = Query(None, description="用户ID"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
):
    """查询系统日志"""
    offset = (page - 1) * page_size

    conditions = []
    params = []

    if start_time:
        conditions.append("timestamp >= ?")
        params.append(start_time)
    if end_time:
        conditions.append("timestamp <= ?")
        params.append(end_time)
    if level:
        conditions.append("level = ?")
        params.append(level.upper())
    if event_type:
        conditions.append("event_type = ?")
        params.append(event_type.upper())
    if trace_id:
        conditions.append("trace_id = ?")
        params.append(trace_id)
    if user_id:
        conditions.append("user_id = ?")
        params.append(user_id)
    if keyword:
        conditions.append("content LIKE ?")
        params.append(f"%{keyword}%")

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    try:
        async with get_db() as db:
            count_cursor = await db.execute(
                f"SELECT COUNT(*) FROM system_logs WHERE {where_clause}",
                params,
            )
            total_row = await count_cursor.fetchone()
            total = total_row[0] if total_row else 0

            query_cursor = await db.execute(
                f"""SELECT id, timestamp, level, event_type, trace_id, user_id, session_id, content
                    FROM system_logs
                    WHERE {where_clause}
                    ORDER BY timestamp DESC
                    LIMIT ? OFFSET ?""",
                params + [page_size, offset],
            )
            rows = await query_cursor.fetchall()

            items = [
                LogEntry(
                    id=row[0],
                    timestamp=row[1],
                    level=row[2],
                    event_type=row[3],
                    trace_id=row[4],
                    user_id=row[5],
                    session_id=row[6],
                    content=row[7],
                )
                for row in rows
            ]

            aggregations = None
            if page == 1:
                agg_cursor = await db.execute(
                    f"""SELECT level, COUNT(*) as count
                        FROM system_logs
                        WHERE {where_clause}
                        GROUP BY level""",
                    params,
                )
                level_rows = await agg_cursor.fetchall()
                logs_by_level = {row[0]: row[1] for row in level_rows}

                agg_cursor = await db.execute(
                    f"""SELECT event_type, COUNT(*) as count
                        FROM system_logs
                        WHERE {where_clause}
                        GROUP BY event_type""",
                    params,
                )
                type_rows = await agg_cursor.fetchall()
                logs_by_type = {row[0]: row[1] for row in type_rows}

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
    start_time: Optional[str] = Query(None, description="开始时间 (ISO8601)"),
    end_time: Optional[str] = Query(None, description="结束时间 (ISO8601)"),
    user_id: Optional[str] = Query(None, description="用户ID"),
    action: Optional[str] = Query(None, description="操作类型"),
    resource_type: Optional[str] = Query(None, description="资源类型"),
    result: Optional[str] = Query(None, description="结果"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
):
    """查询审计日志"""
    offset = (page - 1) * page_size

    conditions = []
    params = []

    if start_time:
        conditions.append("timestamp >= ?")
        params.append(start_time)
    if end_time:
        conditions.append("timestamp <= ?")
        params.append(end_time)
    if user_id:
        conditions.append("user_id = ?")
        params.append(user_id)
    if action:
        conditions.append("action = ?")
        params.append(action.upper())
    if resource_type:
        conditions.append("resource_type = ?")
        params.append(resource_type.lower())
    if result:
        conditions.append("result = ?")
        params.append(result.upper())

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    try:
        async with get_db() as db:
            count_cursor = await db.execute(
                f"SELECT COUNT(*) FROM audit_logs WHERE {where_clause}",
                params,
            )
            total_row = await count_cursor.fetchone()
            total = total_row[0] if total_row else 0

            query_cursor = await db.execute(
                f"""SELECT id, timestamp, user_id, action, resource_type, resource_id, result, client_ip, details
                    FROM audit_logs
                    WHERE {where_clause}
                    ORDER BY timestamp DESC
                    LIMIT ? OFFSET ?""",
                params + [page_size, offset],
            )
            rows = await query_cursor.fetchall()

            items = [
                AuditLogEntry(
                    id=row[0],
                    timestamp=row[1],
                    user_id=row[2],
                    action=row[3],
                    resource_type=row[4],
                    resource_id=row[5],
                    result=row[6],
                    client_ip=row[7],
                    details=json.loads(row[8]) if row[8] else None,
                )
                for row in rows
            ]

            return AuditLogQueryResponse(total=total, items=items)

    except Exception as e:
        logger.error("Failed to query audit logs: %s", e)
        return AuditLogQueryResponse(total=0, items=[])


@router.get("/logs/stats", response_model=LogStatsResponse)
async def get_log_stats():
    """获取日志统计信息"""
    try:
        async with get_db() as db:
            total_cursor = await db.execute("SELECT COUNT(*) FROM system_logs")
            total_row = await total_cursor.fetchone()
            total_logs = total_row[0] if total_row else 0

            level_cursor = await db.execute(
                "SELECT level, COUNT(*) FROM system_logs GROUP BY level"
            )
            level_rows = await level_cursor.fetchall()
            logs_by_level = {row[0]: row[1] for row in level_rows}

            type_cursor = await db.execute(
                "SELECT event_type, COUNT(*) FROM system_logs GROUP BY event_type"
            )
            type_rows = await type_cursor.fetchall()
            logs_by_event_type = {row[0]: row[1] for row in type_rows}

            now = datetime.utcnow()
            last_24h = (now - timedelta(hours=24)).isoformat()
            last_7d = (now - timedelta(days=7)).isoformat()

            cursor_24h = await db.execute(
                "SELECT COUNT(*) FROM system_logs WHERE timestamp >= ?", (last_24h,)
            )
            row_24h = await cursor_24h.fetchone()
            logs_last_24h = row_24h[0] if row_24h else 0

            cursor_7d = await db.execute(
                "SELECT COUNT(*) FROM system_logs WHERE timestamp >= ?", (last_7d,)
            )
            row_7d = await cursor_7d.fetchone()
            logs_last_7d = row_7d[0] if row_7d else 0

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
    start_time: Optional[str] = Query(None, description="开始时间 (ISO8601)"),
    end_time: Optional[str] = Query(None, description="结束时间 (ISO8601)"),
    level: Optional[str] = Query(None, description="日志级别"),
    event_type: Optional[str] = Query(None, description="事件类型"),
    sanitize: bool = Query(True, description="是否脱敏处理"),
):
    """导出日志文件"""
    conditions = []
    params = []

    if start_time:
        conditions.append("timestamp >= ?")
        params.append(start_time)
    if end_time:
        conditions.append("timestamp <= ?")
        params.append(end_time)
    if level:
        conditions.append("level = ?")
        params.append(level.upper())
    if event_type:
        conditions.append("event_type = ?")
        params.append(event_type.upper())

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    try:
        async with get_db() as db:
            cursor = await db.execute(
                f"""SELECT id, timestamp, level, event_type, trace_id, user_id, session_id, content
                    FROM system_logs
                    WHERE {where_clause}
                    ORDER BY timestamp DESC
                    LIMIT 10000""",
                params,
            )
            rows = await cursor.fetchall()

            logs = []
            for row in rows:
                log_entry = {
                    "id": row[0],
                    "timestamp": row[1],
                    "level": row[2],
                    "event_type": row[3],
                    "trace_id": row[4],
                    "user_id": row[5],
                    "session_id": row[6],
                    "content": sanitize_content(row[7]) if sanitize else row[7],
                }
                logs.append(log_entry)

            export_data = {
                "export_time": datetime.utcnow().isoformat(),
                "total_count": len(logs),
                "sanitized": sanitize,
                "logs": logs,
            }

            json_content = json.dumps(export_data, ensure_ascii=False, indent=2)
            buffer = BytesIO(json_content.encode("utf-8"))

            filename = f"yumi_logs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"

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
    start_time: Optional[str] = Query(None, description="开始时间 (ISO8601)"),
    end_time: Optional[str] = Query(None, description="结束时间 (ISO8601)"),
    action: Optional[str] = Query(None, description="操作类型"),
    sanitize: bool = Query(True, description="是否脱敏处理"),
):
    """导出审计日志文件"""
    conditions = []
    params = []

    if start_time:
        conditions.append("timestamp >= ?")
        params.append(start_time)
    if end_time:
        conditions.append("timestamp <= ?")
        params.append(end_time)
    if action:
        conditions.append("action = ?")
        params.append(action.upper())

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    try:
        async with get_db() as db:
            cursor = await db.execute(
                f"""SELECT id, timestamp, user_id, action, resource_type, resource_id, result, client_ip, details
                    FROM audit_logs
                    WHERE {where_clause}
                    ORDER BY timestamp DESC
                    LIMIT 10000""",
                params,
            )
            rows = await cursor.fetchall()

            logs = []
            for row in rows:
                details = json.loads(row[8]) if row[8] else None
                if sanitize and details:
                    details_str = json.dumps(details, ensure_ascii=False)
                    details_str = sanitize_content(details_str)
                    details = json.loads(details_str)

                log_entry = {
                    "id": row[0],
                    "timestamp": row[1],
                    "user_id": row[2],
                    "action": row[3],
                    "resource_type": row[4],
                    "resource_id": row[5],
                    "result": row[6],
                    "client_ip": row[7],
                    "details": details,
                }
                logs.append(log_entry)

            export_data = {
                "export_time": datetime.utcnow().isoformat(),
                "total_count": len(logs),
                "sanitized": sanitize,
                "audit_logs": logs,
            }

            json_content = json.dumps(export_data, ensure_ascii=False, indent=2)
            buffer = BytesIO(json_content.encode("utf-8"))

            filename = f"yumi_audit_logs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"

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
