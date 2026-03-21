"""
Proxy Settings API Router
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..core import get_logger
from ..database import get_db

router = APIRouter()
logger = get_logger(__name__)

# 常见代理端口：Clash(7890), SOCKS5(1080), V2Ray(10809), 7891, 8080, 8118
PROXY_SCAN_PORTS = [7890, 1080, 10809, 7891, 8080, 8118]


class ProxySettingsRequest(BaseModel):
    """代理配置请求体（camelCase 与前端一致）"""

    enabled: bool = False
    mode: str = "smart"
    smartSubMode: str = "auto"
    manualProxyHost: str = ""
    manualProxyPort: int = Field(7890, ge=1, le=65535)
    scannedProxies: list[str] = Field(default_factory=list)
    normalProxyUrl: str = ""


def _settings_to_response(data: dict[str, Any]) -> dict[str, Any]:
    """将数据库 snake_case 转为 API camelCase"""
    return {
        "enabled": data.get("enabled", False),
        "mode": data.get("mode", "smart"),
        "smartSubMode": data.get("smart_sub_mode", "auto"),
        "manualProxyHost": data.get("manual_proxy_host", ""),
        "manualProxyPort": data.get("manual_proxy_port", 7890),
        "scannedProxies": data.get("scanned_proxies", []),
        "normalProxyUrl": data.get("normal_proxy_url", ""),
    }


def _request_to_storage(data: ProxySettingsRequest | dict[str, Any]) -> dict[str, Any]:
    """将 API camelCase 转为存储用 snake_case"""
    if isinstance(data, ProxySettingsRequest):
        return {
            "enabled": data.enabled,
            "mode": data.mode,
            "smart_sub_mode": data.smartSubMode,
            "manual_proxy_host": data.manualProxyHost,
            "manual_proxy_port": data.manualProxyPort,
            "scanned_proxies": data.scannedProxies,
            "normal_proxy_url": data.normalProxyUrl,
        }
    return {
        "enabled": data.get("enabled", False),
        "mode": data.get("mode", "smart"),
        "smart_sub_mode": data.get("smartSubMode", "auto"),
        "manual_proxy_host": data.get("manualProxyHost", ""),
        "manual_proxy_port": int(data.get("manualProxyPort", 7890)),
        "scanned_proxies": data.get("scannedProxies", []),
        "normal_proxy_url": data.get("normalProxyUrl", ""),
    }


async def _check_port(port: int) -> str | None:
    """检测端口是否可用，返回代理 URL 或 None"""
    import socket

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        result = sock.connect_ex(("127.0.0.1", port))
        sock.close()
        if result == 0:
            # HTTP 代理常用端口
            if port in (7890, 7891, 8080, 8118):
                return f"http://127.0.0.1:{port}"
            # SOCKS5 常用端口
            if port == 1080:
                return f"socks5://127.0.0.1:{port}"
            # 默认尝试 HTTP
            return f"http://127.0.0.1:{port}"
    except Exception:
        pass
    return None


@router.get("/settings/proxy")
async def get_proxy_settings():
    """获取代理配置"""
    async with get_db() as db:
        cursor = await db.execute("SELECT value FROM settings WHERE key = ?", ("proxy_settings",))
        row = await cursor.fetchone()
        if row and row[0]:
            try:
                data = json.loads(row[0])
                return _settings_to_response(data)
            except json.JSONDecodeError:
                logger.warning("Invalid proxy_settings JSON in database")
        return _settings_to_response({})


@router.put("/settings/proxy")
async def update_proxy_settings(settings: ProxySettingsRequest):
    """更新代理配置"""
    storage = _request_to_storage(settings)
    async with get_db() as db:
        await db.execute(
            """INSERT OR REPLACE INTO settings (key, value, updated_at)
               VALUES (?, ?, CURRENT_TIMESTAMP)""",
            ("proxy_settings", json.dumps(storage, ensure_ascii=False)),
        )
        await db.commit()
    logger.info(
        "Proxy settings updated: enabled=%s, mode=%s",
        storage["enabled"],
        storage["mode"],
    )
    return _settings_to_response(storage)


@router.post("/proxy/scan")
async def scan_proxy_ports():
    """扫描本地常见代理端口"""
    logger.info("Starting proxy port scan", extra={"ports": PROXY_SCAN_PORTS})
    results: list[str] = []
    for port in PROXY_SCAN_PORTS:
        url = await _check_port(port)
        if url:
            results.append(url)
            logger.debug("Proxy found on port %d: %s", port, url)
    logger.info("Proxy scan completed", extra={"found": len(results), "urls": results})
    return results
