"""
Model Management API Router
"""
from __future__ import annotations

import base64
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import httpx
from cryptography.fernet import Fernet
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..core import clear_active_model, get_logger, set_active_model
from ..core.model_state import get_active_model as get_active_model_state
from ..services.log_service import AuditAction, log_service
from ..services.proxy_config import get_proxy_config

router = APIRouter()
logger = get_logger(__name__)

_ENCRYPTION_KEY: bytes | None = None
_KEY_FILE = Path(__file__).parent.parent.parent / "data" / ".encryption_key"


def _clean_base_url(url: str) -> str:
    """清理并规范化 base URL"""
    if not url:
        return ""
    url = url.strip()
    url = url.rstrip(",;:")
    url = url.rstrip("/")
    return url


def _get_encryption_key() -> bytes:
    global _ENCRYPTION_KEY
    if _ENCRYPTION_KEY is not None:
        return _ENCRYPTION_KEY

    key_str = os.environ.get("YUMI_ENCRYPTION_KEY")
    if key_str:
        _ENCRYPTION_KEY = base64.urlsafe_b64decode(key_str.encode())
        return _ENCRYPTION_KEY

    if _KEY_FILE.exists():
        try:
            _ENCRYPTION_KEY = _KEY_FILE.read_bytes()
            logger.debug("Loaded encryption key from file")
            return _ENCRYPTION_KEY
        except Exception as e:
            logger.warning("Failed to read encryption key file: %s", e)

    _ENCRYPTION_KEY = Fernet.generate_key()
    try:
        _KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
        _KEY_FILE.write_bytes(_ENCRYPTION_KEY)
        logger.info("Generated and saved new encryption key")
    except Exception as e:
        logger.warning("Failed to save encryption key file: %s", e)

    return _ENCRYPTION_KEY


def _get_fernet() -> Fernet:
    return Fernet(_get_encryption_key())


class ModelConfig(BaseModel):
    id: str | None = None
    providerId: str = "custom"
    name: str
    baseUrl: str
    apiKey: str = ""
    modelName: str
    customModelName: str | None = None
    modelType: str = "text"
    maxTokens: int = 4096
    temperature: float = 0.85
    isEnabled: bool = False
    isTested: bool = False
    testStatus: str = "untested"
    lastTestAt: str | None = None
    lastTestMessage: str | None = None
    editCount: int = 0
    createdAt: str | None = None
    updatedAt: str | None = None
    apiKeyUnchanged: bool = False


class ModelTestRequest(BaseModel):
    baseUrl: str
    apiKey: str
    modelName: str
    testMessage: str | None = "你好，请简单介绍一下你自己。"
    verbose: bool = True


class ModelTestResponse(BaseModel):
    success: bool
    message: str
    response: str | None = None
    latency: float | None = None


def encrypt_api_key(api_key: str) -> str:
    if not api_key:
        return ""
    try:
        fernet = _get_fernet()
        encrypted = fernet.encrypt(api_key.encode())
        return f"enc:{base64.urlsafe_b64encode(encrypted).decode()}"
    except Exception as e:
        logger.error("Failed to encrypt API key: %s", e)
        return ""


def decrypt_api_key(encrypted_key: str) -> str:
    if not encrypted_key:
        return ""
    if not encrypted_key.startswith("enc:"):
        return encrypted_key
    try:
        fernet = _get_fernet()
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_key[4:].encode())
        return fernet.decrypt(encrypted_bytes).decode()
    except Exception as e:
        logger.error("Failed to decrypt API key: %s", e)
        return ""


def mask_api_key(api_key: str) -> str:
    """掩码显示 API Key，仅显示前4位和后4位"""
    if not api_key or len(api_key) < 8:
        return "****"
    return f"{api_key[:4]}****{api_key[-4:]}"


@router.get("/models", response_model=list[ModelConfig])
async def get_models(accountId: str = Query(..., min_length=1)):
    from ..database import get_db

    try:
        async with get_db() as db:
            cursor = await db.execute(
                """SELECT id, provider_id, name, base_url, api_key, model_name,
                          custom_model_name, model_type, max_tokens, temperature,
                          is_enabled, is_tested, test_status, last_test_at,
                          last_test_message, edit_count, created_at, updated_at
                   FROM model_configs
                   WHERE account_id = ?
                   ORDER BY created_at DESC""",
                (accountId,),
            )
            rows = await cursor.fetchall()

            return [
                ModelConfig(
                    id=row[0],
                    providerId=row[1],
                    name=row[2],
                    baseUrl=row[3],
                    apiKey=mask_api_key(decrypt_api_key(row[4])) if row[4] else "",
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
async def create_model(config: ModelConfig, accountId: str = Query(..., min_length=1)):
    from ..database import get_db

    model_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    display_name = config.name.strip() if config.name and config.name.strip() else None

    if not display_name:
        display_name = await _generate_unique_name(config.modelName, accountId)

    try:
        async with get_db() as db:
            await db.execute(
                """INSERT INTO model_configs
                   (id, account_id, provider_id, name, base_url, api_key, model_name,
                    custom_model_name, model_type, max_tokens, temperature,
                    is_enabled, is_tested, test_status, edit_count, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    model_id,
                    accountId,
                    config.providerId,
                    display_name,
                    _clean_base_url(config.baseUrl),
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
            config.name = display_name
            config.createdAt = now
            config.updatedAt = now

            await log_service.log_audit(
                action=AuditAction.MODEL_KEY_ADD,
                resource_type="model",
                resource_id=model_id,
                result="SUCCESS",
                details={"provider": config.providerId, "name": display_name},
            )

            return config
    except Exception as e:
        logger.error("Failed to create model: %s", e)
        await log_service.log_audit(
            action=AuditAction.MODEL_KEY_ADD,
            resource_type="model",
            resource_id=None,
            result="FAIL",
            details={"error": str(e)},
        )
        raise


async def _generate_unique_name(base_name: str, account_id: str) -> str:
    """生成唯一的显示名称，如果重复则添加数字编号"""
    from ..database import get_db

    try:
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT name FROM model_configs WHERE account_id = ? AND name LIKE ?",
                (account_id, f"{base_name}%"),
            )
            rows = await cursor.fetchall()

            if not rows:
                return base_name

            existing_names = {row[0] for row in rows}
            if base_name not in existing_names:
                return base_name

            counter = 2
            while f"{base_name} {counter}" in existing_names:
                counter += 1

            return f"{base_name} {counter}"
    except Exception as e:
        logger.error("Failed to generate unique name: %s", e)
        return base_name


@router.put("/models/{model_id}", response_model=ModelConfig)
async def update_model(model_id: str, config: ModelConfig, accountId: str = Query(..., min_length=1)):
    from ..database import get_db

    now = datetime.utcnow().isoformat()

    display_name = config.name.strip() if config.name and config.name.strip() else None

    if not display_name:
        display_name = await _generate_unique_name_for_update(model_id, config.modelName, accountId)

    try:
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT edit_count, api_key FROM model_configs WHERE id = ? AND account_id = ?",
                (model_id, accountId),
            )
            row = await cursor.fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="模型不存在")
            current_edit_count = row[0] if row else 0
            existing_api_key = row[1] if row else ""

            if config.apiKeyUnchanged:
                api_key_to_save = existing_api_key
            else:
                api_key_to_save = encrypt_api_key(config.apiKey)

            await db.execute(
                """UPDATE model_configs
                   SET provider_id = ?, name = ?, base_url = ?, api_key = ?,
                       model_name = ?, custom_model_name = ?, model_type = ?,
                       max_tokens = ?, temperature = ?, is_enabled = ?,
                       edit_count = ?, updated_at = ?
                   WHERE id = ? AND account_id = ?""",
                (
                    config.providerId,
                    display_name,
                    _clean_base_url(config.baseUrl),
                    api_key_to_save,
                    config.modelName,
                    config.customModelName,
                    config.modelType,
                    config.maxTokens,
                    config.temperature,
                    1 if config.isEnabled and api_key_to_save else 0,
                    current_edit_count + 1,
                    now,
                    model_id,
                    accountId,
                ),
            )
            await db.commit()

            config.id = model_id
            config.name = display_name
            config.editCount = current_edit_count + 1
            config.updatedAt = now

            await log_service.log_audit(
                action=AuditAction.MODEL_KEY_UPDATE,
                resource_type="model",
                resource_id=model_id,
                result="SUCCESS",
                details={"name": display_name, "api_key_changed": not config.apiKeyUnchanged},
            )

            return config
    except Exception as e:
        logger.error("Failed to update model: %s", e)
        await log_service.log_audit(
            action=AuditAction.MODEL_KEY_UPDATE,
            resource_type="model",
            resource_id=model_id,
            result="FAIL",
            details={"error": str(e)},
        )
        raise


async def _generate_unique_name_for_update(exclude_id: str, base_name: str, account_id: str) -> str:
    """生成唯一的显示名称（更新时排除当前记录）"""
    from ..database import get_db

    try:
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT name FROM model_configs WHERE account_id = ? AND name LIKE ? AND id != ?",
                (account_id, f"{base_name}%", exclude_id),
            )
            rows = await cursor.fetchall()

            if not rows:
                return base_name

            existing_names = {row[0] for row in rows}
            if base_name not in existing_names:
                return base_name

            counter = 2
            while f"{base_name} {counter}" in existing_names:
                counter += 1

            return f"{base_name} {counter}"
    except Exception as e:
        logger.error("Failed to generate unique name for update: %s", e)
        return base_name


@router.delete("/models/{model_id}")
async def delete_model(model_id: str, accountId: str = Query(..., min_length=1)):
    from ..database import get_db

    try:
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT name FROM model_configs WHERE id = ? AND account_id = ?",
                (model_id, accountId),
            )
            row = await cursor.fetchone()
            model_name = row[0] if row else None

            await db.execute("DELETE FROM model_configs WHERE id = ? AND account_id = ?", (model_id, accountId))
            await db.commit()

            await log_service.log_audit(
                action=AuditAction.MODEL_KEY_DELETE,
                resource_type="model",
                resource_id=model_id,
                result="SUCCESS",
                details={"name": model_name},
            )

            return {"success": True, "message": "模型已删除"}
    except Exception as e:
        logger.error("Failed to delete model: %s", e)
        await log_service.log_audit(
            action=AuditAction.MODEL_KEY_DELETE,
            resource_type="model",
            resource_id=model_id,
            result="FAIL",
            details={"error": str(e)},
        )
        raise


@router.post("/models/{model_id}/enable")
async def enable_model(model_id: str, accountId: str = Query(..., min_length=1)):
    from ..database import get_db

    try:
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT api_key, name, provider_id, base_url, model_name FROM model_configs WHERE id = ? AND account_id = ?",
                (model_id, accountId),
            )
            row = await cursor.fetchone()

            if not row:
                await log_service.log_audit(
                    action=AuditAction.MODEL_ENABLE,
                    resource_type="model",
                    resource_id=model_id,
                    result="FAIL",
                    details={"reason": "model_not_found"},
                )
                return {"success": False, "message": "模型不存在"}

            api_key, name, provider_id, base_url, model_name = row

            if not api_key:
                await log_service.log_audit(
                    action=AuditAction.MODEL_ENABLE,
                    resource_type="model",
                    resource_id=model_id,
                    result="FAIL",
                    details={"reason": "no_api_key", "name": name},
                )
                return {"success": False, "message": "请先配置 API 密钥"}

            now = datetime.now(timezone.utc).isoformat()
            await db.execute(
                "UPDATE model_configs SET is_enabled = 1, updated_at = ? WHERE id = ? AND account_id = ?",
                (now, model_id, accountId),
            )
            await db.commit()

            await log_service.log_audit(
                action=AuditAction.MODEL_ENABLE,
                resource_type="model",
                resource_id=model_id,
                result="SUCCESS",
                details={"name": name},
            )

            return {"success": True, "message": "模型已启用"}
    except Exception as e:
        logger.error("Failed to enable model: %s", e)
        await log_service.log_audit(
            action=AuditAction.MODEL_ENABLE,
            resource_type="model",
            resource_id=model_id,
            result="FAIL",
            details={"error": str(e)},
        )
        raise


@router.post("/models/{model_id}/disable")
async def disable_model(model_id: str, accountId: str = Query(..., min_length=1)):
    from ..database import get_db

    try:
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT name FROM model_configs WHERE id = ? AND account_id = ?",
                (model_id, accountId),
            )
            row = await cursor.fetchone()
            model_name = row[0] if row else None

            await db.execute(
                "UPDATE model_configs SET is_enabled = 0, updated_at = ? WHERE id = ? AND account_id = ?",
                (datetime.utcnow().isoformat(), model_id, accountId),
            )
            await db.commit()

            active_model = get_active_model_state(accountId)
            if active_model and active_model.get("model_id") == model_id:
                clear_active_model(accountId)

            await log_service.log_audit(
                action=AuditAction.MODEL_DISABLE,
                resource_type="model",
                resource_id=model_id,
                result="SUCCESS",
                details={"name": model_name},
            )

            return {"success": True, "message": "模型已禁用"}
    except Exception as e:
        logger.error("Failed to disable model: %s", e)
        await log_service.log_audit(
            action=AuditAction.MODEL_DISABLE,
            resource_type="model",
            resource_id=model_id,
            result="FAIL",
            details={"error": str(e)},
        )
        raise


@router.post("/models/{model_id}/set_active")
async def set_active_model_endpoint(model_id: str, accountId: str = Query(..., min_length=1)):
    from ..database import get_db

    try:
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT api_key, name, provider_id, base_url, model_name, is_enabled FROM model_configs WHERE id = ? AND account_id = ?",
                (model_id, accountId),
            )
            row = await cursor.fetchone()

            if not row:
                return {"success": False, "message": "模型不存在"}

            api_key, name, provider_id, base_url, model_name, is_enabled = row

            if not api_key:
                return {"success": False, "message": "请先配置 API 密钥"}

            if not is_enabled:
                return {"success": False, "message": "请先启用该模型"}

            model_config = {
                "model_id": model_id,
                "provider_id": provider_id,
                "base_url": base_url,
                "api_key": decrypt_api_key(api_key),
                "model_name": model_name,
                "display_name": name,
            }
            set_active_model(accountId, model_config)

            await log_service.log_audit(
                action=AuditAction.MODEL_ENABLE,
                resource_type="model",
                resource_id=model_id,
                result="SUCCESS",
                details={"action": "set_active", "name": name},
            )

            return {"success": True, "message": f"已切换到模型: {name}"}
    except Exception as e:
        logger.error("Failed to set active model: %s", e)
        raise


@router.post("/test", response_model=ModelTestResponse)
async def test_model(request: ModelTestRequest):
    from ..services.llm import LLMService

    llm_service = LLMService()
    cleaned_url = _clean_base_url(request.baseUrl)

    try:
        success, message, content, latency = await llm_service.test_connection(
            provider_id="custom",
            base_url=cleaned_url,
            api_key=request.apiKey,
            model_name=request.modelName,
            test_message=request.testMessage or "你好，请简单介绍一下你自己。",
        )

        if request.verbose:
            return ModelTestResponse(
                success=success,
                message=message,
                response=content,
                latency=latency,
            )
        else:
            return ModelTestResponse(
                success=success,
                message=message,
                latency=latency,
            )
    except Exception as e:
        logger.error("Model test error: %s", e)
        return ModelTestResponse(
            success=False,
            message=f"测试失败: {str(e)}",
        )


class ModelTestByIdRequest(BaseModel):
    verbose: bool = True


@router.post("/models/{model_id}/test")
async def test_model_by_id(
    model_id: str,
    request: ModelTestByIdRequest = None,  # type: ignore[assignment]
    accountId: str = Query(..., min_length=1),
):
    from ..database import get_db

    verbose = request.verbose if request else True
    logger.info("Testing model by id: %s, verbose: %s", model_id, verbose)

    try:
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT base_url, api_key, model_name FROM model_configs WHERE id = ? AND account_id = ?",
                (model_id, accountId),
            )
            row = await cursor.fetchone()

            if not row:
                return {"success": False, "message": "模型不存在"}

            base_url, encrypted_key, model_name = row
            api_key = decrypt_api_key(encrypted_key) if encrypted_key else ""

            if not api_key:
                return {"success": False, "message": "请先配置 API 密钥"}

            test_result = await _perform_test(base_url, api_key, model_name, verbose)
            now = datetime.utcnow().isoformat()

            await db.execute(
                """UPDATE model_configs
                   SET is_tested = ?, test_status = ?, last_test_at = ?,
                       last_test_message = ?, updated_at = ?
                   WHERE id = ? AND account_id = ?""",
                (
                    1 if test_result["success"] else 0,
                    "passed" if test_result["success"] else "failed",
                    now,
                    test_result["message"],
                    now,
                    model_id,
                    accountId,
                ),
            )
            await db.commit()

            return test_result
    except Exception as e:
        logger.error("Failed to test model: %s", e)
        raise


async def _perform_test(
    base_url: str, api_key: str, model_name: str, verbose: bool = True
) -> dict:
    cleaned_url = _clean_base_url(base_url)
    url = f"{cleaned_url}/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

    if verbose:
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": "你好，请简单介绍一下你自己。"}],
            "max_tokens": 1024,
        }
    else:
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 5,
        }

    proxy_config = await get_proxy_config()
    proxy = None
    if proxy_config.enabled and proxy_config.mode == "normal":
        proxy = proxy_config.get_normal_proxy()
    trust_env = proxy is not None
    try:
        start_time = time.time()
        async with httpx.AsyncClient(timeout=60.0, proxy=proxy, trust_env=trust_env) as client:
            response = await client.post(url, json=payload, headers=headers)
            latency = time.time() - start_time

            if response.status_code == 200:
                if verbose:
                    data = response.json()
                    choices = data.get("choices", [])
                    if choices:
                        message = choices[0].get("message", {})
                        content = message.get("content")
                        reasoning_content = message.get("reasoning_content")
                        if content or reasoning_content:
                            return {
                                "success": True,
                                "message": f"连接成功 ({latency:.3f}s)",
                                "latency": latency,
                                "response": content,
                                "reasoning": reasoning_content,
                            }
                    return {
                        "success": True,
                        "message": f"连接成功 ({latency:.3f}s) - 无内容返回",
                        "latency": latency,
                        "response": None,
                        "reasoning": None,
                    }
                else:
                    return {
                        "success": True,
                        "message": f"测试成功 ({latency:.3f}s)",
                        "latency": latency,
                        "response": None,
                        "reasoning": None,
                    }
            else:
                return {
                    "success": False,
                    "message": f"测试失败: HTTP {response.status_code}",
                    "response": None,
                    "reasoning": None,
                }
    except httpx.TimeoutException as e:
        logger.error(
            "Model test timeout: url=%s, error=%s (type=%s)",
            url, str(e), type(e).__name__,
            exc_info=True,
        )
        return {"success": False, "message": "测试失败: 连接超时", "response": None, "reasoning": None}
    except httpx.ConnectError as e:
        logger.error(
            "Model test ConnectError: url=%s, error=%s (type=%s)",
            url, str(e), type(e).__name__,
            exc_info=True,
        )
        return {
            "success": False,
            "message": "测试失败: 无法连接服务器，请检查网络或代理配置",
            "response": None,
            "reasoning": None,
        }
    except Exception as e:
        logger.error(
            "Model test error: url=%s, error=%s (type=%s)",
            url, str(e), type(e).__name__,
            exc_info=True,
        )
        return {"success": False, "message": f"测试失败: {str(e)}", "response": None, "reasoning": None}


@router.get("/active", response_model=ModelConfig | None)
async def get_active_model(accountId: str = Query(..., min_length=1)):
    from ..database import get_db

    try:
        async with get_db() as db:
            cursor = await db.execute(
                """SELECT id, provider_id, name, base_url, api_key, model_name,
                          custom_model_name, model_type, max_tokens, temperature,
                          is_enabled, is_tested, test_status, last_test_at,
                          last_test_message, edit_count, created_at, updated_at
                   FROM model_configs
                   WHERE account_id = ? AND is_enabled = 1
                   LIMIT 1""",
                (accountId,),
            )
            row = await cursor.fetchone()

            if row:
                return ModelConfig(
                    id=row[0],
                    providerId=row[1],
                    name=row[2],
                    baseUrl=row[3],
                    apiKey=mask_api_key(decrypt_api_key(row[4])) if row[4] else "",
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
