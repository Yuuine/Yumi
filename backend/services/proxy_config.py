"""
Proxy configuration - reads from database
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

from ..database import get_db

# Max retries for smart proxy
SMART_PROXY_MAX_RETRIES = 5


@dataclass
class ProxyConfig:
    """代理配置（供 model_adapters 使用）"""

    enabled: bool = False
    mode: str = "smart"  # smart | normal
    smart_sub_mode: str = "auto"  # auto | manual
    manual_proxy_host: str = ""
    manual_proxy_port: int = 7890
    scanned_proxies: list[str] = field(default_factory=list)
    normal_proxy_url: str = ""

    def get_proxy_urls_for_fallback(self) -> list[str]:
        """获取智能代理的备用代理列表（最多 5 个）"""
        if self.mode != "smart":
            return []
        urls: list[str] = []
        if self.smart_sub_mode == "manual":
            if self.manual_proxy_host and self.manual_proxy_port > 0:
                urls.append(f"http://{self.manual_proxy_host}:{self.manual_proxy_port}")
        else:
            urls = list(self.scanned_proxies)[:SMART_PROXY_MAX_RETRIES]
        return urls

    def get_normal_proxy(self) -> str | None:
        """获取普通代理 URL"""
        if self.mode != "normal" or not self.normal_proxy_url:
            return None
        return self.normal_proxy_url.strip() or None


async def get_proxy_config() -> ProxyConfig:
    """从数据库读取代理配置"""
    try:
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT value FROM settings WHERE key = ?", ("proxy_settings",)
            )
            row = await cursor.fetchone()
            if row and row[0]:
                data = json.loads(row[0])
                return ProxyConfig(
                    enabled=data.get("enabled", False),
                    mode=data.get("mode", "smart"),
                    smart_sub_mode=data.get("smart_sub_mode", "auto"),
                    manual_proxy_host=data.get("manual_proxy_host", ""),
                    manual_proxy_port=int(data.get("manual_proxy_port", 7890)),
                    scanned_proxies=data.get("scanned_proxies", []),
                    normal_proxy_url=data.get("normal_proxy_url", ""),
                )
    except Exception:
        pass
    return ProxyConfig()
