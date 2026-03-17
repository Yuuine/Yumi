"""
Model Management API Router
"""
from __future__ import annotations

import base64
import logging
import time
import uuid
from datetime import datetime
from typing import Optional

import httpx
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)


class ModelConfig(BaseModel):
    id: Optional[str] = None
    providerId: str = "custom"
    name: str
    baseUrl: str
    apiKey: str = ""
    modelName: str
    customModelName: Optional[str] = None
    modelType: str = "text"
    maxTokens: int = 4096
    temperature: float = 0.85
    isEnabled: bool = False
    isTested: bool = False
    testStatus: str = "untested"
    lastTestAt: Optional[str] = None
    lastTestMessage: Optional[str] = None
    editCount: int = 0
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None


class ModelTestRequest(BaseModel):
    baseUrl: str
    apiKey: str
    modelName: str
    testMessage: Optional[str] = "你好，请简单介绍一下你自己。"


class ModelTestResponse(BaseModel):
    success: bool
    message: str
    response: Optional[str] = None
    latency: Optional[float] = None


def encrypt_api_key(api_key: str) -> str:
    if not api_key:
        return ""
    encoded = base64.b64encode(api_key.encode()).decode()
    return f"enc:{encoded}"


def decrypt_api_key(encrypted_key: str) -> str:
    if not encrypted_key or not encrypted_key.startswith("enc:"):
        return encrypted_key or ""
    try:
        return base64.b64decode(encrypted_key[4:]).decode()
    except Exception:
        return ""


@router.get("/models", response_model=list[ModelConfig])
async def get_models():
    from ..database import get_db

    try:
        async with await get_db() as db:
            cursor = await db.execute(
                """SELECT id, provider_id, name, base_url, api_key, model_name,
                          custom_model_name, model_type, max_tokens, temperature,
                          is_enabled, is_tested, test_status, last_test_at,
                          last_test_message, edit_count, created_at, updated_at
                   FROM model_configs
                   ORDER BY created_at DESC"""
            )
            rows = await cursor.fetchall()

            return [
                ModelConfig(
                    id=row[0],
                    providerId=row[1],
                    name=row[2],
                    baseUrl=row[3],
                    apiKey=decrypt_api_key(row[4]) if row[4] else "",
                    modelName=row[5],
                    customModelName=row[6],
                    modelType=row[7] or "text",
                    maxTokens=row[8],
                    temperature=row[9],
                    isEnabled=bool(row[10]),
                    isTested=bool(row[11]),
                    testStatus=row[12] or "untested",
                    lastTestAt=row[13],
                    lastTestMessage=row[14],
                    editCount=row[15] or 0,
                    createdAt=row[16],
                    updatedAt=row[17],
                )
                for row in rows
            ]
    except Exception as e:
        logger.error("Failed to get models: %s", e)
        return []


@router.post("/models", response_model=ModelConfig)
async def create_model(config: ModelConfig):
    from ..database import get_db

    model_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    try:
        async with await get_db() as db:
            await db.execute(
                """INSERT INTO model_configs 
                   (id, provider_id, name, base_url, api_key, model_name, 
                    custom_model_name, model_type, max_tokens, temperature, 
                    is_enabled, is_tested, test_status, edit_count, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    model_id,
                    config.providerId,
                    config.name,
                    config.baseUrl.rstrip("/"),
                    encrypt_api_key(config.apiKey),
                    config.modelName,
                    config.customModelName,
                    config.modelType,
                    config.maxTokens,
                    config.temperature,
                    1 if config.isEnabled and config.apiKey else 0,
                    0,
                    "untested",
                    0,
                    now,
                    now,
                ),
            )
            await db.commit()

            config.id = model_id
            config.createdAt = now
            config.updatedAt = now
            return config
    except Exception as e:
        logger.error("Failed to create model: %s", e)
        raise


@router.put("/models/{model_id}", response_model=ModelConfig)
async def update_model(model_id: str, config: ModelConfig):
    from ..database import get_db

    now = datetime.utcnow().isoformat()

    try:
        async with await get_db() as db:
            cursor = await db.execute(
                "SELECT edit_count FROM model_configs WHERE id = ?", (model_id,)
            )
            row = await cursor.fetchone()
            current_edit_count = row[0] if row else 0

            await db.execute(
                """UPDATE model_configs 
                   SET provider_id = ?, name = ?, base_url = ?, api_key = ?, 
                       model_name = ?, custom_model_name = ?, model_type = ?,
                       max_tokens = ?, temperature = ?, is_enabled = ?,
                       edit_count = ?, updated_at = ?
                   WHERE id = ?""",
                (
                    config.providerId,
                    config.name,
                    config.baseUrl.rstrip("/"),
                    encrypt_api_key(config.apiKey),
                    config.modelName,
                    config.customModelName,
                    config.modelType,
                    config.maxTokens,
                    config.temperature,
                    1 if config.isEnabled and config.apiKey else 0,
                    current_edit_count + 1,
                    now,
                    model_id,
                ),
            )
            await db.commit()

            config.id = model_id
            config.editCount = current_edit_count + 1
            config.updatedAt = now
            return config
    except Exception as e:
        logger.error("Failed to update model: %s", e)
        raise


@router.delete("/models/{model_id}")
async def delete_model(model_id: str):
    from ..database import get_db

    try:
        async with await get_db() as db:
            await db.execute("DELETE FROM model_configs WHERE id = ?", (model_id,))
            await db.commit()

            return {"success": True, "message": "模型已删除"}
    except Exception as e:
        logger.error("Failed to delete model: %s", e)
        raise


@router.post("/models/{model_id}/enable")
async def enable_model(model_id: str):
    from ..database import get_db

    try:
        async with await get_db() as db:
            cursor = await db.execute(
                "SELECT api_key FROM model_configs WHERE id = ?", (model_id,)
            )
            row = await cursor.fetchone()

            if not row:
                return {"success": False, "message": "模型不存在"}

            if not row[0]:
                return {"success": False, "message": "请先配置 API 密钥"}

            await db.execute(
                "UPDATE model_configs SET is_enabled = 1, updated_at = ? WHERE id = ?",
                (datetime.utcnow().isoformat(), model_id),
            )
            await db.commit()

            return {"success": True, "message": "模型已启用"}
    except Exception as e:
        logger.error("Failed to enable model: %s", e)
        raise


@router.post("/models/{model_id}/disable")
async def disable_model(model_id: str):
    from ..database import get_db

    try:
        async with await get_db() as db:
            await db.execute(
                "UPDATE model_configs SET is_enabled = 0, updated_at = ? WHERE id = ?",
                (datetime.utcnow().isoformat(), model_id),
            )
            await db.commit()

            return {"success": True, "message": "模型已禁用"}
    except Exception as e:
        logger.error("Failed to disable model: %s", e)
        raise


@router.post("/test", response_model=ModelTestResponse)
async def test_model(request: ModelTestRequest):
    url = f"{request.baseUrl.rstrip('/')}/chat/completions"

    headers = {"Content-Type": "application/json"}
    if request.apiKey:
        headers["Authorization"] = f"Bearer {request.apiKey}"

    payload = {
        "model": request.modelName,
        "messages": [
            {"role": "user", "content": request.testMessage},
        ],
        "max_tokens": 100,
        "temperature": 0.7,
    }

    try:
        start_time = time.time()
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            latency = time.time() - start_time

            if response.status_code != 200:
                return ModelTestResponse(
                    success=False,
                    message=f"API 返回错误: HTTP {response.status_code}",
                    latency=latency,
                )

            data = response.json()
            
            choices = data.get("choices", [])
            if not choices:
                return ModelTestResponse(
                    success=False,
                    message="API 返回数据格式错误: 缺少 choices",
                    latency=latency,
                )
            
            message = choices[0].get("message", {})
            
            content = message.get("content")
            reasoning_content = message.get("reasoning_content")
            
            response_parts = []
            if reasoning_content:
                response_parts.append(f"**推理过程:**\n{reasoning_content}")
            if content:
                response_parts.append(f"**回答:**\n{content}")
            
            if response_parts:
                final_response = "\n\n".join(response_parts)
            else:
                final_response = "模型返回成功，但无内容输出"
            
            return ModelTestResponse(
                success=True,
                message="连接成功",
                response=final_response,
                latency=round(latency, 2),
            )

    except httpx.TimeoutException:
        return ModelTestResponse(
            success=False,
            message="连接超时，请检查网络或 API 地址",
        )
    except httpx.ConnectError:
        return ModelTestResponse(
            success=False,
            message="无法连接到服务器，请检查 API 地址是否正确",
        )
    except Exception as e:
        logger.error("Model test error: %s", e)
        return ModelTestResponse(
            success=False,
            message=f"测试失败: {str(e)}",
        )


@router.post("/models/{model_id}/test")
async def test_model_by_id(model_id: str):
    from ..database import get_db

    try:
        async with await get_db() as db:
            cursor = await db.execute(
                "SELECT base_url, api_key, model_name FROM model_configs WHERE id = ?",
                (model_id,),
            )
            row = await cursor.fetchone()

            if not row:
                return {"success": False, "message": "模型不存在"}

            base_url, encrypted_key, model_name = row
            api_key = decrypt_api_key(encrypted_key) if encrypted_key else ""

            if not api_key:
                return {"success": False, "message": "请先配置 API 密钥"}

            test_result = await _perform_test(base_url, api_key, model_name)
            now = datetime.utcnow().isoformat()

            await db.execute(
                """UPDATE model_configs 
                   SET is_tested = ?, test_status = ?, last_test_at = ?, 
                       last_test_message = ?, updated_at = ?
                   WHERE id = ?""",
                (
                    1 if test_result["success"] else 0,
                    "passed" if test_result["success"] else "failed",
                    now,
                    test_result["message"],
                    now,
                    model_id,
                ),
            )
            await db.commit()

            return test_result
    except Exception as e:
        logger.error("Failed to test model: %s", e)
        raise


async def _perform_test(base_url: str, api_key: str, model_name: str) -> dict:
    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": "你好"}],
        "max_tokens": 50,
    }

    try:
        start_time = time.time()
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            latency = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                choices = data.get("choices", [])
                if choices:
                    message = choices[0].get("message", {})
                    has_content = message.get("content") or message.get("reasoning_content")
                    if has_content:
                        return {
                            "success": True,
                            "message": f"连接成功 ({latency:.2f}s)",
                            "latency": latency,
                        }
                return {
                    "success": True,
                    "message": f"连接成功 ({latency:.2f}s) - 无内容返回",
                    "latency": latency,
                }
            else:
                return {
                    "success": False,
                    "message": f"HTTP {response.status_code}",
                }
    except httpx.TimeoutException:
        return {"success": False, "message": "连接超时"}
    except httpx.ConnectError:
        return {"success": False, "message": "无法连接服务器"}
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.get("/active", response_model=Optional[ModelConfig])
async def get_active_model():
    from ..database import get_db

    try:
        async with await get_db() as db:
            cursor = await db.execute(
                """SELECT id, provider_id, name, base_url, api_key, model_name,
                          custom_model_name, model_type, max_tokens, temperature,
                          is_enabled, is_tested, test_status, last_test_at,
                          last_test_message, edit_count, created_at, updated_at
                   FROM model_configs
                   WHERE is_enabled = 1
                   LIMIT 1"""
            )
            row = await cursor.fetchone()

            if row:
                return ModelConfig(
                    id=row[0],
                    providerId=row[1],
                    name=row[2],
                    baseUrl=row[3],
                    apiKey=decrypt_api_key(row[4]) if row[4] else "",
                    modelName=row[5],
                    customModelName=row[6],
                    modelType=row[7] or "text",
                    maxTokens=row[8],
                    temperature=row[9],
                    isEnabled=bool(row[10]),
                    isTested=bool(row[11]),
                    testStatus=row[12] or "untested",
                    lastTestAt=row[13],
                    lastTestMessage=row[14],
                    editCount=row[15] or 0,
                    createdAt=row[16],
                    updatedAt=row[17],
                )
            return None
    except Exception as e:
        logger.error("Failed to get active model: %s", e)
        return None
