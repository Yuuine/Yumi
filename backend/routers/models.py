"""
Model Management API Router
基于新数据库设计重构，使用 SQLModel
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
from sqlmodel import select

from ..core import clear_active_model, get_logger, set_active_model
from ..core.model_state import get_active_model as get_active_model_state
from ..database_sqlmodel import get_session
from ..models import ModelConfig as ModelConfigModel, ModelProvider
from ..services.log_service import AuditAction, log_service

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


def _model_to_response(model: ModelConfigModel) -> ModelConfig:
    """将数据库模型转换为响应模型"""
    return ModelConfig(
        id=model.id,
        providerId=model.provider_id,
        name=model.name,
        baseUrl=model.base_url,
        apiKey=mask_api_key(decrypt_api_key(model.api_key)) if model.api_key else "",
        modelName=model.model_name,
        customModelName=model.custom_model_name,
        modelType=model.model_type or "text",
        maxTokens=model.max_tokens or 4096,
        temperature=model.temperature or 0.85,
        isEnabled=bool(model.is_enabled),
        isTested=bool(model.is_tested),
        testStatus=model.test_status or "untested",
        lastTestAt=model.last_test_at.isoformat() if model.last_test_at else None,
        lastTestMessage=model.last_test_message,
        editCount=model.edit_count or 0,
        createdAt=model.created_at.isoformat() if model.created_at else None,
        updatedAt=model.updated_at.isoformat() if model.updated_at else None,
    )


@router.get("/models", response_model=list[ModelConfig])
async def get_models(accountId: str = Query(..., min_length=1)):
    """获取用户的所有模型配置"""
    try:
        async with get_session() as session:
            result = await session.exec(
                select(ModelConfigModel)
                .where(ModelConfigModel.account_id == accountId)
                .order_by(ModelConfigModel.created_at.desc())
            )
            models = result.all()
            return [_model_to_response(m) for m in models]
    except Exception as e:
        logger.error("Failed to get models: %s", e)
        return []


@router.post("/models", response_model=ModelConfig)
async def create_model(config: ModelConfig, accountId: str = Query(..., min_length=1)):
    """创建新模型配置"""
    model_id = str(uuid.uuid4())
    now = datetime.utcnow()

    display_name = config.name.strip() if config.name and config.name.strip() else None
    if not display_name:
        display_name = await _generate_unique_name(config.modelName, accountId)

    try:
        async with get_session() as session:
            new_model = ModelConfigModel(
                id=model_id,
                account_id=accountId,
                provider_id=config.providerId,
                name=display_name,
                base_url=_clean_base_url(config.baseUrl),
                api_key=encrypt_api_key(config.apiKey),
                model_name=config.modelName,
                custom_model_name=config.customModelName,
                model_type=config.modelType,
                max_tokens=config.maxTokens,
                temperature=config.temperature,
                is_enabled=1 if config.isEnabled and config.apiKey else 0,
                is_tested=False,
                test_status="untested",
                edit_count=0,
                created_at=now,
                updated_at=now,
            )
            session.add(new_model)
            await session.commit()
            await session.refresh(new_model)

            await log_service.log_audit(
                action=AuditAction.MODEL_KEY_ADD,
                resource_type="model",
                resource_id=model_id,
                result="SUCCESS",
                details={"provider": config.providerId, "name": display_name},
            )

            return _model_to_response(new_model)
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
    try:
        async with get_session() as session:
            result = await session.exec(
                select(ModelConfigModel.name)
                .where(ModelConfigModel.account_id == account_id)
                .where(ModelConfigModel.name.like(f"{base_name}%"))
            )
            existing_names = {row for row in result.all()}

            if not existing_names or base_name not in existing_names:
                return base_name

            counter = 2
            while f"{base_name} {counter}" in existing_names:
                counter += 1

            return f"{base_name} {counter}"
    except Exception as e:
        logger.error("Failed to generate unique name: %s", e)
        return base_name


@router.put("/models/{model_id}", response_model=ModelConfig)
async def update_model(
    model_id: str, config: ModelConfig, accountId: str = Query(..., min_length=1)
):
    """更新模型配置"""
    now = datetime.utcnow()

    display_name = config.name.strip() if config.name and config.name.strip() else None
    if not display_name:
        display_name = await _generate_unique_name_for_update(model_id, config.modelName, accountId)

    try:
        async with get_session() as session:
            result = await session.exec(
                select(ModelConfigModel)
                .where(ModelConfigModel.id == model_id)
                .where(ModelConfigModel.account_id == accountId)
            )
            existing_model = result.first()

            if not existing_model:
                raise HTTPException(status_code=404, detail="模型不存在")

            # 更新字段
            existing_model.provider_id = config.providerId
            existing_model.name = display_name
            existing_model.base_url = _clean_base_url(config.baseUrl)
            existing_model.model_name = config.modelName
            existing_model.custom_model_name = config.customModelName
            existing_model.model_type = config.modelType
            existing_model.max_tokens = config.maxTokens
            existing_model.temperature = config.temperature
            existing_model.edit_count = (existing_model.edit_count or 0) + 1
            existing_model.updated_at = now

            # 处理 API Key
            if not config.apiKeyUnchanged:
                existing_model.api_key = encrypt_api_key(config.apiKey)

            # 更新启用状态（必须有 API Key）
            if config.isEnabled and existing_model.api_key:
                existing_model.is_enabled = True
            elif not config.isEnabled:
                existing_model.is_enabled = False

            await session.commit()
            await session.refresh(existing_model)

            await log_service.log_audit(
                action=AuditAction.MODEL_KEY_UPDATE,
                resource_type="model",
                resource_id=model_id,
                result="SUCCESS",
                details={"name": display_name, "api_key_changed": not config.apiKeyUnchanged},
            )

            return _model_to_response(existing_model)
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
    try:
        async with get_session() as session:
            result = await session.exec(
                select(ModelConfigModel.name)
                .where(ModelConfigModel.account_id == account_id)
                .where(ModelConfigModel.name.like(f"{base_name}%"))
                .where(ModelConfigModel.id != exclude_id)
            )
            existing_names = {row for row in result.all()}

            if not existing_names or base_name not in existing_names:
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
    """删除模型配置"""
    try:
        async with get_session() as session:
            result = await session.exec(
                select(ModelConfigModel)
                .where(ModelConfigModel.id == model_id)
                .where(ModelConfigModel.account_id == accountId)
            )
            model = result.first()

            if not model:
                raise HTTPException(status_code=404, detail="模型不存在")

            model_name = model.name
            await session.delete(model)
            await session.commit()

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
    """启用模型"""
    try:
        async with get_session() as session:
            result = await session.exec(
                select(ModelConfigModel)
                .where(ModelConfigModel.id == model_id)
                .where(ModelConfigModel.account_id == accountId)
            )
            model = result.first()

            if not model:
                await log_service.log_audit(
                    action=AuditAction.MODEL_ENABLE,
                    resource_type="model",
                    resource_id=model_id,
                    result="FAIL",
                    details={"reason": "model_not_found"},
                )
                return {"success": False, "message": "模型不存在"}

            if not model.api_key:
                await log_service.log_audit(
                    action=AuditAction.MODEL_ENABLE,
                    resource_type="model",
                    resource_id=model_id,
                    result="FAIL",
                    details={"reason": "no_api_key", "name": model.name},
                )
                return {"success": False, "message": "请先配置 API 密钥"}

            model.is_enabled = True
            model.updated_at = datetime.utcnow()
            await session.commit()

            await log_service.log_audit(
                action=AuditAction.MODEL_ENABLE,
                resource_type="model",
                resource_id=model_id,
                result="SUCCESS",
                details={"name": model.name},
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
    """禁用模型"""
    try:
        async with get_session() as session:
            result = await session.exec(
                select(ModelConfigModel)
                .where(ModelConfigModel.id == model_id)
                .where(ModelConfigModel.account_id == accountId)
            )
            model = result.first()

            if not model:
                return {"success": False, "message": "模型不存在"}

            model.is_enabled = False
            model.updated_at = datetime.utcnow()
            await session.commit()

            # 清除活动模型缓存
            active_model = get_active_model_state(accountId)
            if active_model and active_model.get("model_id") == model_id:
                clear_active_model(accountId)

            await log_service.log_audit(
                action=AuditAction.MODEL_DISABLE,
                resource_type="model",
                resource_id=model_id,
                result="SUCCESS",
                details={"name": model.name},
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
    """设置活动模型"""
    try:
        async with get_session() as session:
            result = await session.exec(
                select(ModelConfigModel)
                .where(ModelConfigModel.id == model_id)
                .where(ModelConfigModel.account_id == accountId)
            )
            model = result.first()

            if not model:
                return {"success": False, "message": "模型不存在"}

            if not model.api_key:
                return {"success": False, "message": "请先配置 API 密钥"}

            if not model.is_enabled:
                return {"success": False, "message": "请先启用该模型"}

            model_config = {
                "model_id": model_id,
                "provider_id": model.provider_id,
                "base_url": model.base_url,
                "api_key": decrypt_api_key(model.api_key),
                "model_name": model.model_name,
                "display_name": model.name,
            }
            set_active_model(accountId, model_config)

            await log_service.log_audit(
                action=AuditAction.MODEL_ENABLE,
                resource_type="model",
                resource_id=model_id,
                result="SUCCESS",
                details={"action": "set_active", "name": model.name},
            )

            return {"success": True, "message": f"已切换到模型: {model.name}"}
    except Exception as e:
        logger.error("Failed to set active model: %s", e)
        raise


@router.post("/test", response_model=ModelTestResponse)
async def test_model(request: ModelTestRequest):
    """测试模型连接"""
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
    request: ModelTestByIdRequest = None,
    accountId: str = Query(..., min_length=1),
):
    """通过ID测试模型"""
    verbose = request.verbose if request else True
    logger.info("Testing model by id: %s, verbose: %s", model_id, verbose)

    try:
        async with get_session() as session:
            result = await session.exec(
                select(ModelConfigModel)
                .where(ModelConfigModel.id == model_id)
                .where(ModelConfigModel.account_id == accountId)
            )
            model = result.first()

            if not model:
                return {"success": False, "message": "模型不存在"}

            api_key = decrypt_api_key(model.api_key) if model.api_key else ""
            if not api_key:
                return {"success": False, "message": "请先配置 API 密钥"}

            test_result = await _perform_test(model.base_url, api_key, model.model_name, verbose)
            now = datetime.utcnow()

            model.is_tested = test_result["success"]
            model.test_status = "passed" if test_result["success"] else "failed"
            model.last_test_at = now
            model.last_test_message = test_result["message"]
            model.updated_at = now

            await session.commit()

            return test_result
    except Exception as e:
        logger.error("Failed to test model: %s", e)
        raise


async def _perform_test(base_url: str, api_key: str, model_name: str, verbose: bool = True) -> dict:
    """执行模型测试"""
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

    try:
        start_time = time.time()
        async with httpx.AsyncClient(timeout=60.0, trust_env=False) as client:
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
        logger.error("Model test timeout: url=%s, error=%s", url, str(e))
        return {
            "success": False,
            "message": "测试失败: 连接超时",
            "response": None,
            "reasoning": None,
        }
    except httpx.ConnectError as e:
        logger.error("Model test ConnectError: url=%s, error=%s", url, str(e))
        return {
            "success": False,
            "message": "测试失败: 无法连接服务器，请检查网络或代理配置",
            "response": None,
            "reasoning": None,
        }
    except Exception as e:
        logger.error("Model test error: url=%s, error=%s", url, str(e))
        return {
            "success": False,
            "message": f"测试失败: {str(e)}",
            "response": None,
            "reasoning": None,
        }


@router.get("/active", response_model=ModelConfig | None)
async def get_active_model(accountId: str = Query(..., min_length=1)):
    """获取当前活动模型"""
    try:
        async with get_session() as session:
            result = await session.exec(
                select(ModelConfigModel)
                .where(ModelConfigModel.account_id == accountId)
                .where(ModelConfigModel.is_enabled == True)
                .limit(1)
            )
            model = result.first()

            if model:
                return _model_to_response(model)
            return None
    except Exception as e:
        logger.error("Failed to get active model: %s", e)
        return None
