# Yumi API

## 目录

1. [概述](#1-概述)
2. [通用说明](#2-通用说明)
3. [聊天 API](#3-聊天-api)
4. [记忆 API](#4-记忆-api)
5. [角色卡 API](#5-角色卡-api)
6. [模型管理 API](#6-模型管理-api)
7. [用户 API](#7-用户-api)
8. [设置 API](#8-设置-api)
9. [代理 API](#9-代理-api)
10. [缓存 API](#10-缓存-api)
11. [存储 API](#11-存储-api)
12. [日志 API](#12-日志-api)
13. [健康检查](#13-健康检查)

---

## 文档导航

| 相关文档 | 说明 |
|---------|------|
| [项目 README](../README.md) | 项目概览、快速开始 |
| [架构设计](./architecture.md) | 系统整体架构、模块划分 |
| [记忆引擎](./memory-engine.md) | 记忆引擎详细设计 |
| [情绪引擎](./emotion-engine.md) | 情绪引擎详细设计 |

---

## 1. 概述

Yumi API 是基于 FastAPI 的 RESTful API，用于支持 Yumi AI 的后端服务。

### 基础信息

| 项 | 说明 |
|----|------|
| **API 前缀** | `/api` |
| **数据格式** | JSON |
| **字符编码** | UTF-8 |
| **认证方式** | 本地账户系统 |

---

## 2. 通用说明

### 2.1 通用响应格式

所有 API 响应均采用 JSON 格式。

### 2.2 错误处理

| HTTP 状态码 | 说明 |
|------------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 3. 聊天 API

### 3.1 发送聊天消息

```
POST /api/chat
```

**请求体**：

```json
{
  "userId": "string",
  "conversationId": "string (可选)",
  "characterId": "string (可选)",
  "message": "string",
  "temperature": 0.85 (可选, 0.0-2.0),
  "stream": false (可选),
  "deepThinking": false (可选)
}
```

**响应**：

```json
{
  "reply": "string",
  "emotion": {
    "valence": 0.5,
    "arousal": 0.5,
    "label": "neutral"
  },
  "memoryUsed": 6,
  "newSummary": "string (可选)",
  "conversationId": "string (可选)"
}
```

---

### 3.2 流式聊天响应

```
GET /api/chat/stream
```

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| userId | string | 是 | 用户 ID |
| message | string | 是 | 消息内容 |
| conversationId | string | 否 | 会话 ID |
| characterId | string | 否 | 角色卡 ID |
| temperature | float | 否 | 温度参数 (默认 0.85) |
| deepThinking | boolean | 否 | 是否深度思考 (默认 false) |

**响应**：Server-Sent Events (SSE)

---

### 3.3 获取聊天历史

```
GET /api/chat/history
```

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| userId | string | 是 | 用户 ID |
| conversationId | string | 是 | 会话 ID；仅返回该会话下的消息（缺省时返回空列表） |
| limit | int | 否 | 返回数量 (默认 50) |
| offset | int | 否 | 偏移量 (默认 0)，与 `timestamp DESC` 分页配合加载更早消息 |

**响应**：

```json
{
  "messages": [
    {
      "id": "string",
      "role": "user/assistant",
      "content": "string",
      "timestamp": "string",
      "emotion": {
        "valence": 0.5,
        "arousal": 0.5
      } (可选)
    }
  ]
}
```

---

### 3.4 获取会话列表

```
GET /api/conversations
```

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| userId | string | 是 | 用户 ID |
| characterId | string | 否 | 角色卡 ID (筛选) |
| limit | int | 否 | 返回数量 (默认 20) |
| offset | int | 否 | 偏移量 (默认 0) |

**响应**：

```json
{
  "conversations": [...]
}
```

---

### 3.5 获取对话交互日志列表

```
GET /api/dialogue-logs
```

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| userId | string | 是 | 用户 ID |
| limit | int | 否 | 返回数量 (默认 50) |
| offset | int | 否 | 偏移量 (默认 0) |
| includeDetails | boolean | 否 | 是否包含详情 (默认 false) |

**响应**：

```json
{
  "logs": [...],
  "total": 0
}
```

---

### 3.6 获取单条对话交互日志详情

```
GET /api/dialogue-logs/{log_id}
```

**路径参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| log_id | int | 是 | 日志 ID |

---

### 3.7 获取特定会话的对话交互日志

```
GET /api/conversations/{conversation_id}/dialogue-logs
```

**路径参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| conversation_id | string | 是 | 会话 ID |

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| includeDetails | boolean | 否 | 是否包含详情 (默认 false) |
| limit | int | 否 | 返回数量 (默认 100) |
| offset | int | 否 | 偏移量 (默认 0) |

---

### 3.8 清除对话交互日志

```
DELETE /api/dialogue-logs
```

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| userId | string | 否 | 用户 ID，不传则清除所有 |

**响应**：

```json
{
  "deleted_count": 0,
  "user_id": "string (可选)"
}
```

---

### 3.9 获取对话交互日志统计

```
GET /api/dialogue-logs/stats
```

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| userId | string | 否 | 用户 ID，不传则返回所有统计 |

---

## 4. 记忆 API

### 4.1 搜索记忆

```
GET /api/memory/search
```

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| query | string | 是 | 搜索查询 |
| top_k | int | 否 | 返回数量 (默认 6) |
| decay_days | boolean | 否 | 是否应用时间衰减 (默认 true) |

**响应**：

```json
{
  "memories": [
    {
      "id": "string",
      "content": "string",
      "timestamp": "string",
      "similarity": 0.9,
      "decay_factor": 1.0
    }
  ],
  "total": 0
}
```

---

### 4.2 获取记忆统计

```
GET /api/memory/stats
```

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| userId | string | 是 | 用户 ID |

**响应**：

```json
{
  "total_memories": 0,
  "oldest_memory": "string (可选)",
  "newest_memory": "string (可选)",
  "avg_importance": 0.5
}
```

---

## 5. 角色卡 API

### 5.1 获取角色卡列表

```
GET /api/character-cards
```

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| userId | string | 是 | 用户 ID |

**响应**：

```json
[
  {
    "id": "string",
    "userId": "string",
    "conversationId": "string (可选)",
    "roleOverview": "string",
    "formalName": "string",
    "nickname": "string",
    "raceOrForm": "string",
    "gender": "string",
    "visualAge": "string",
    "actualAge": "string",
    "location": "string",
    "appearanceDesc": "string",
    "corePersonality": "string",
    "selfPerception": "string",
    "attitudeToUser": "string",
    "likes": "string",
    "dislikes": "string",
    "toneBase": "string",
    "wordHabits": "string",
    "emotionRules": "string",
    "lengthPref": "string",
    "specialLogicList": "string",
    "fewShotExamples": "string",
    "isActive": true
  }
]
```

---

### 5.2 更新单个角色卡

```
PUT /api/character-cards/{card_id}
```

**路径参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| card_id | string | 是 | 角色卡 ID |

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| userId | string | 是 | 用户 ID |

**请求体**：角色卡对象（同上）

**响应**：

```json
{
  "success": true,
  "id": "string"
}
```

---

### 5.3 批量更新角色卡

```
PUT /api/character-cards/batch
```

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| userId | string | 是 | 用户 ID |

**请求体**：

```json
{
  "cards": [
    {
      "id": "string",
      "...": "其他角色卡字段"
    }
  ]
}
```

**响应**：

```json
{
  "success": true,
  "count": 0
}
```

---

### 5.4 删除角色卡

```
DELETE /api/character-cards/{card_id}
```

**路径参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| card_id | string | 是 | 角色卡 ID |

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| userId | string | 是 | 用户 ID |

**响应**：

```json
{
  "success": true,
  "id": "string"
}
```

---

## 6. 模型管理 API

### 6.1 获取模型列表

```
GET /api/models
```

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| accountId | string | 是 | 账户 ID |

**响应**：

```json
[
  {
    "id": "string",
    "providerId": "string",
    "name": "string",
    "baseUrl": "string",
    "apiKey": "string (掩码)",
    "modelName": "string",
    "customModelName": "string (可选)",
    "modelType": "string",
    "maxTokens": 4096,
    "temperature": 0.85,
    "isEnabled": false,
    "isTested": false,
    "testStatus": "untested",
    "lastTestAt": "string (可选)",
    "lastTestMessage": "string (可选)",
    "editCount": 0,
    "createdAt": "string (可选)",
    "updatedAt": "string (可选)",
    "apiKeyUnchanged": false
  }
]
```

---

### 6.2 创建模型

```
POST /api/models
```

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| accountId | string | 是 | 账户 ID |

**请求体**：模型配置对象（同上）

**响应**：模型配置对象（同上）

---

### 6.3 更新模型

```
PUT /api/models/{model_id}
```

**路径参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| model_id | string | 是 | 模型 ID |

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| accountId | string | 是 | 账户 ID |

**请求体**：模型配置对象（同上）

**响应**：模型配置对象（同上）

---

### 6.4 删除模型

```
DELETE /api/models/{model_id}
```

**路径参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| model_id | string | 是 | 模型 ID |

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| accountId | string | 是 | 账户 ID |

**响应**：

```json
{
  "success": true,
  "message": "模型已删除"
}
```

---

### 6.5 启用模型

```
POST /api/models/{model_id}/enable
```

**路径参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| model_id | string | 是 | 模型 ID |

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| accountId | string | 是 | 账户 ID |

**响应**：

```json
{
  "success": true,
  "message": "模型已启用"
}
```

---

### 6.6 禁用模型

```
POST /api/models/{model_id}/disable
```

**路径参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| model_id | string | 是 | 模型 ID |

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| accountId | string | 是 | 账户 ID |

**响应**：

```json
{
  "success": true,
  "message": "模型已禁用"
}
```

---

### 6.7 设置当前活动模型

```
POST /api/models/{model_id}/set_active
```

**路径参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| model_id | string | 是 | 模型 ID |

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| accountId | string | 是 | 账户 ID |

**响应**：

```json
{
  "success": true,
  "message": "已切换到模型: {name}"
}
```

---

### 6.8 测试模型连接（通用）

```
POST /api/test
```

**请求体**：

```json
{
  "baseUrl": "string",
  "apiKey": "string",
  "modelName": "string",
  "testMessage": "string (可选)",
  "verbose": true (可选)
}
```

**响应**：

```json
{
  "success": true,
  "message": "string",
  "response": "string (可选)",
  "latency": 0.5 (可选)
}
```

---

### 6.9 测试已保存模型

```
POST /api/models/{model_id}/test
```

**路径参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| model_id | string | 是 | 模型 ID |

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| accountId | string | 是 | 账户 ID |

**请求体**：

```json
{
  "verbose": true (可选)
}
```

---

### 6.10 获取当前活动模型

```
GET /api/active
```

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| accountId | string | 是 | 账户 ID |

**响应**：模型配置对象或 null

---

## 7. 用户 API

### 7.1 获取用户配置

```
GET /api/user/profile
```

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| userId | string | 是 | 用户 ID |

**响应**：

```json
{
  "id": "string",
  "roleName": "string",
  "preferences": {
    "communicationStyle": "warm",
    "topicsOfInterest": ["生活", "工作", "情感"],
    "emotionalSupportLevel": "high",
    "responseLength": "medium"
  }
}
```

---

### 7.2 更新用户配置

```
PUT /api/user/profile
```

**请求体**：用户配置对象（同上）

**响应**：用户配置对象（同上）

---

### 7.3 清除用户数据

```
POST /api/user/purge
```

**请求体**：

```json
{
  "userId": "string"
}
```

**响应**：

```json
{
  "success": true,
  "cleared": {
    "memories": 0,
    "conversation_logs": 0,
    "conversations": 0,
    "memory_summaries": 0,
    "character_cards": 0,
    "audit_logs": 0,
    "system_logs": 0,
    "user_profile": 0,
    "model_configs": 0
  }
}
```

---

## 8. 设置 API

### 8.1 获取应用设置

```
GET /api/settings
```

**响应**：

```json
{
  "api_endpoint": "http://127.0.0.1:11434/v1",
  "api_key": "",
  "model_name": "llama3.1:8b",
  "max_tokens": 4096,
  "temperature": 0.85,
  "memory_enabled": true,
  "emotion_detection": true,
  "theme": "light",
  "language": "zh-CN"
}
```

---

### 8.2 更新应用设置

```
PUT /api/settings
```

**请求体**：应用设置对象（同上）

**响应**：应用设置对象（同上）

---

## 9. 代理 API

### 9.1 获取代理配置

```
GET /api/settings/proxy
```

**响应**：

```json
{
  "enabled": false,
  "mode": "smart",
  "smartSubMode": "auto",
  "manualProxyHost": "",
  "manualProxyPort": 7890,
  "scannedProxies": [],
  "normalProxyUrl": ""
}
```

---

### 9.2 更新代理配置

```
PUT /api/settings/proxy
```

**请求体**：代理配置对象（同上）

**响应**：代理配置对象（同上）

---

### 9.3 扫描本地代理端口

```
POST /api/proxy/scan
```

**响应**：扫描到的代理 URL 列表

```json
["http://127.0.0.1:7890", "socks5://127.0.0.1:1080"]
```

---

## 10. 缓存 API

### 10.1 获取所有缓存统计

```
GET /api/cache/stats
```

**响应**：

```json
{
  "success": true,
  "data": {
    "cache_name": {
      "hits": 0,
      "misses": 0,
      "requests": 0,
      "hit_rate": 0.0
    }
  }
}
```

---

### 10.2 获取指定缓存统计

```
GET /api/cache/stats/{name}
```

**路径参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 缓存名称 |

**响应**：

```json
{
  "success": true,
  "data": {
    "hits": 0,
    "misses": 0,
    "requests": 0,
    "hit_rate": 0.0
  }
}
```

---

### 10.3 重置所有缓存统计

```
POST /api/cache/stats/reset
```

**响应**：

```json
{
  "success": true,
  "message": "Cache stats reset successfully"
}
```

---

### 10.4 重置指定缓存统计

```
POST /api/cache/stats/{name}/reset
```

**路径参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 缓存名称 |

**响应**：

```json
{
  "success": true,
  "message": "Cache '{name}' stats reset successfully"
}
```

---

### 10.5 获取缓存服务信息

```
GET /api/cache/info
```

**响应**：

```json
{
  "success": true,
  "data": {
    "total_hits": 0,
    "total_misses": 0,
    "total_requests": 0,
    "overall_hit_rate": 0.0,
    "caches": ["cache1", "cache2"]
  }
}
```

---

## 11. 存储 API

### 11.1 获取指定任务的存储状态

```
GET /api/storage/status/{task_id}
```

**路径参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| task_id | string | 是 | 任务 ID |

**响应**：

```json
{
  "taskId": "string",
  "status": "pending/completed/failed",
  "dbStored": false,
  "vectorStored": false,
  "attempts": 0,
  "storedAt": "string (可选)"
}
```

---

### 11.2 获取存储队列统计

```
GET /api/storage/stats
```

**响应**：

```json
{
  "queueLength": 0,
  "avgLatencyMs": 0.0,
  "successCount": 0,
  "failureCount": 0,
  "retryCount": 0
}
```

---

## 12. 日志 API

### 12.1 查询系统日志

```
GET /api/logs
```

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| start_time | string | 否 | 开始时间 (ISO8601) |
| end_time | string | 否 | 结束时间 (ISO8601) |
| level | string | 否 | 日志级别 |
| event_type | string | 否 | 事件类型 |
| trace_id | string | 否 | 追踪 ID |
| user_id | string | 否 | 用户 ID |
| keyword | string | 否 | 关键词搜索 |
| page | int | 否 | 页码 (默认 1) |
| page_size | int | 否 | 每页数量 (默认 50, 最大 200) |

**响应**：

```json
{
  "total": 0,
  "items": [
    {
      "id": 0,
      "timestamp": "string",
      "level": "string",
      "event_type": "string",
      "trace_id": "string (可选)",
      "user_id": "string (可选)",
      "session_id": "string (可选)",
      "content": "string"
    }
  ],
  "aggregations": {
    "byLevel": {},
    "byEventType": {}
  } (可选)
}
```

---

### 12.2 查询审计日志

```
GET /api/logs/audit
```

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| start_time | string | 否 | 开始时间 (ISO8601) |
| end_time | string | 否 | 结束时间 (ISO8601) |
| user_id | string | 否 | 用户 ID |
| action | string | 否 | 操作类型 |
| resource_type | string | 否 | 资源类型 |
| result | string | 否 | 结果 |
| page | int | 否 | 页码 (默认 1) |
| page_size | int | 否 | 每页数量 (默认 50, 最大 200) |

**响应**：

```json
{
  "total": 0,
  "items": [
    {
      "id": 0,
      "timestamp": "string",
      "user_id": "string (可选)",
      "action": "string",
      "resource_type": "string",
      "resource_id": "string (可选)",
      "result": "string",
      "client_ip": "string (可选)",
      "details": {} (可选)
    }
  ]
}
```

---

### 12.3 获取日志统计

```
GET /api/logs/stats
```

**响应**：

```json
{
  "total_logs": 0,
  "logs_by_level": {},
  "logs_by_event_type": {},
  "logs_last_24h": 0,
  "logs_last_7d": 0
}
```

---

### 12.4 导出系统日志

```
GET /api/logs/export
```

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| start_time | string | 否 | 开始时间 (ISO8601) |
| end_time | string | 否 | 结束时间 (ISO8601) |
| level | string | 否 | 日志级别 |
| event_type | string | 否 | 事件类型 |
| sanitize | boolean | 否 | 是否脱敏 (默认 true) |

**响应**：JSON 文件下载

---

### 12.5 导出审计日志

```
GET /api/logs/audit/export
```

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| start_time | string | 否 | 开始时间 (ISO8601) |
| end_time | string | 否 | 结束时间 (ISO8601) |
| action | string | 否 | 操作类型 |
| sanitize | boolean | 否 | 是否脱敏 (默认 true) |

**响应**：JSON 文件下载

---

## 13. 健康检查

### 13.1 健康检查

```
GET /health
```

**响应**：

```json
{
  "status": "healthy"
}
```

---

## 附录

### A. 情绪数据模型

```json
{
  "valence": 0.5,
  "arousal": 0.5,
  "label": "neutral"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| valence | float | 效价 (0.0-1.0, 消极-积极) |
| arousal | float | 唤醒度 (0.0-1.0, 平静-激动) |
| label | string | 情绪标签 |
