# Yumi - AI虚拟人物伴侣 Code Wiki

## 目录
- [项目概述](#1-项目概述)
- [技术栈与架构](#2-技术栈与架构)
- [项目结构](#3-项目结构)
- [核心模块说明](#4-核心模块说明)
- [数据模型设计](#5-数据模型设计)
- [API接口](#6-api接口)
- [开发与部署](#7-开发与部署)
- [关键类与函数](#8-关键类与函数)

---

## 1. 项目概述

### 1.1 项目简介
Yumi 是一个基于 AI 的虚拟人物伴侣应用，强调隐私优先、情感智能和本地化存储。项目采用前端和后端分离的架构，同时支持桌面应用（Tauri）和纯 Web 应用模式。

### 1.2 核心理念
- **隐私优先**：所有数据本地存储，不上传云端
- **情感智能**：记忆引擎 + 情绪分析，提供个性化体验
- **角色系统**：支持自定义 AI 角色性格和设定

### 1.3 核心功能
| 功能 | 描述 | 状态 |
|------|------|------|
| 智能对话 | 与 AI 角色进行自然流畅的对话 | 半完成 |
| 记忆引擎 | 基于向量检索的长期记忆系统 | 开发中 |
| 情绪分析 | 基于 V-A 模型的情绪智能 | 开发中 |
| 角色卡系统 | 支持自定义 AI 角色性格 | 已完成 |
| 本地存储 | 所有数据加密存储在本地 | 已完成 |

---

## 2. 技术栈与架构

### 2.1 整体架构
```
┌─────────────────┐
│   用户界面层    │  Vue 3 + TypeScript
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  状态管理层     │  Pinia
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  API 通信层     │  Axios
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  后端服务层     │  FastAPI
└────────┬────────┘
         │
         ├─────────────────────────────┐
         ▼                             ▼
┌─────────────────┐      ┌─────────────────┐
│  业务服务层     │      │  外部 LLM API  │
└────────┬────────┘      └─────────────────┘
         │
         ▼
┌─────────────────┐
│  数据持久层     │  SQLite + ChromaDB
└─────────────────┘
```

### 2.2 技术栈详情

#### 前端技术栈
- **框架**：Vue 3.4 (Composition API)
- **语言**：TypeScript 5.4
- **状态管理**：Pinia 2.1
- **UI 框架**：Element Plus 2.6
- **路由**：Vue Router 4.3
- **构建工具**：Vite 5.1
- **测试**：Vitest 1.5, Playwright
- **代码规范**：ESLint, Prettier

#### 后端技术栈
- **Web 框架**：FastAPI 0.110
- **ORM**：SQLModel (基于 SQLAlchemy 2.0)
- **数据库**：SQLite (主数据库) + ChromaDB (向量数据库)
- **异步处理**：asyncio
- **代码规范**：Ruff, Black, MyPy
- **测试**：pytest

#### 桌面应用
- **框架**：Tauri 2.0
- **语言**：Rust 1.75+

---

## 3. 项目结构

### 3.1 目录树
```
/workspace/
├── backend/                    # 后端代码
│   ├── core/                   # 核心基础设施
│   │   ├── auth.py            # 认证相关
│   │   ├── cache.py           # 缓存
│   │   ├── config.py          # 配置管理
│   │   ├── error_handlers.py  # 错误处理
│   │   ├── exceptions.py      # 异常定义
│   │   ├── lifecycle.py       # 生命周期管理
│   │   ├── logging.py         # 日志系统
│   │   ├── middleware.py      # 中间件
│   │   ├── model_state.py     # 模型状态
│   │   └── security_middleware.py  # 安全中间件
│   ├── models/                 # 数据模型
│   │   ├── user.py
│   │   ├── character_card.py
│   │   ├── conversation.py
│   │   ├── conversation_log.py
│   │   ├── dialogue_interaction_log.py
│   │   ├── memory_summary.py
│   │   ├── model_config.py
│   │   ├── model_provider.py
│   │   ├── setting.py
│   │   ├── audit_log.py
│   │   └── system_log.py
│   ├── routers/                # API 路由
│   │   ├── auth.py
│   │   ├── cache.py
│   │   ├── character_cards.py
│   │   ├── chat.py
│   │   ├── logs.py
│   │   ├── memory.py
│   │   ├── models.py
│   │   ├── settings.py
│   │   ├── storage.py
│   │   └── user.py
│   ├── services/               # 业务服务
│   │   ├── providers/         # 模型提供商适配器
│   │   │   ├── deepseek/
│   │   │   ├── kimi/
│   │   │   ├── openai/
│   │   │   └── base.py
│   │   ├── async_storage.py
│   │   ├── auth_service.py
│   │   ├── cache_service.py
│   │   ├── character_card.py
│   │   ├── conversation_service.py
│   │   ├── dialogue_log_service.py
│   │   ├── emotion.py
│   │   ├── llm.py
│   │   ├── log_service.py
│   │   ├── memory.py
│   │   ├── memory_cache.py
│   │   ├── model_adapters.py
│   │   └── prompt_builder.py
│   ├── tests/                  # 后端测试
│   ├── main.py                 # 后端入口
│   ├── database_sqlmodel.py    # 数据库初始化
│   ├── requirements.txt
│   └── pyproject.toml
├── src/                        # 前端代码
│   ├── api/                    # API 客户端
│   │   ├── auth.ts
│   │   ├── character-cards.ts
│   │   ├── chat.ts
│   │   ├── conversations.ts
│   │   ├── http-client.ts
│   │   ├── models.ts
│   │   └── user.ts
│   ├── components/             # Vue 组件
│   │   ├── chat/
│   │   ├── common/
│   │   ├── icons/
│   │   ├── models/
│   │   ├── settings/
│   │   └── sidebar/
│   ├── composables/            # 组合式函数
│   │   ├── useAsync.ts
│   │   ├── useModal.ts
│   │   ├── useModalState.ts
│   │   └── useToast.ts
│   ├── constants/
│   ├── hooks/
│   ├── router/                 # 路由配置
│   ├── stores/                 # Pinia 状态管理
│   │   ├── account.ts
│   │   ├── auth.ts
│   │   ├── chat.ts
│   │   ├── models.ts
│   │   ├── settings.ts
│   │   └── theme.ts
│   ├── styles/                 # 样式文件
│   ├── types/                  # TypeScript 类型定义
│   ├── utils/                  # 工具函数
│   ├── views/                  # 页面组件
│   │   ├── ChatView.vue
│   │   └── LoginView.vue
│   ├── App.vue
│   └── main.ts                 # 前端入口
├── src-tauri/                  # Tauri 桌面应用
│   ├── src/
│   │   ├── backend/
│   │   ├── commands/
│   │   ├── tray/
│   │   ├── main.rs
│   │   └── lib.rs
│   └── Cargo.toml
├── docs/                       # 文档
├── public/                     # 静态资源
├── .github/
│   └── workflows/
│       └── ci.yml
├── package.json
├── vite.config.ts
└── tsconfig.json
```

---

## 4. 核心模块说明

### 4.1 前端核心模块

#### 4.1.1 状态管理 (Stores)
- **account.ts**：管理账户加密、密钥管理、角色卡、对话历史
- **chat.ts**：管理当前对话、消息列表、生成状态、流式响应处理
- **auth.ts**：管理认证状态、用户登录/登出
- **models.ts**：管理模型列表、模型配置
- **settings.ts**：管理应用设置、UI 状态
- **theme.ts**：管理主题切换

#### 4.1.2 聊天模块 (Chat)
核心文件：[src/stores/chat.ts](file:///workspace/src/stores/chat.ts)

主要功能：
- 消息管理（发送、接收、存储）
- 对话切换与创建
- 历史消息加载
- 流式响应处理（打字机效果）
- 错误处理与重试

关键函数：
- `sendMessage()`：发送非流式消息
- `sendMessageStream()`：发送流式消息
- `switchConversation()`：切换对话
- `startNewConversation()`：开始新对话
- `loadHistory()`：加载历史消息

### 4.2 后端核心模块

#### 4.2.1 LLM 服务 (LLMService)
核心文件：[backend/services/llm.py](file:///workspace/backend/services/llm.py)

主要功能：
- 调用外部 LLM API
- 支持流式和非流式响应
- 模型连接测试
- 多模型提供商支持

关键方法：
- `chat()`：非流式对话
- `stream_chat()`：流式对话
- `test_connection()`：测试模型连接
- `get_adapter()`：获取模型适配器

#### 4.2.2 记忆引擎 (MemoryEngine)
核心文件：[backend/services/memory.py](file:///workspace/backend/services/memory.py)

主要功能：
- 向量存储与检索
- 语义去重
- 记忆衰减（艾宾浩斯遗忘曲线）
- 对话摘要（支持 LLM 摘要）
- 记忆重要性评分

关键方法：
- `store()`：存储记忆
- `search()`：检索相关记忆
- `get_recent()`：获取近期记忆
- `summarize_with_llm()`：使用 LLM 生成摘要
- `_calculate_decay()`：计算记忆衰减因子

#### 4.2.3 情绪引擎 (EmotionEngine)
核心文件：[backend/services/emotion.py](file:///workspace/backend/services/emotion.py)

主要功能：
- 基于 V-A（效价-唤醒度）模型的情绪分析
- 双重情绪系统（即时情绪 + 背景情绪）

#### 4.2.4 提示构建器 (PromptBuilder)
核心文件：[backend/services/prompt_builder.py](file:///workspace/backend/services/prompt_builder.py)

主要功能：
- 整合多源信息构建 LLM 提示
- 角色卡信息集成
- 历史对话集成
- 记忆检索结果集成
- 情绪状态集成

#### 4.2.5 模型适配器 (ModelAdapters)
核心文件：[backend/services/model_adapters.py](file:///workspace/backend/services/model_adapters.py)

设计模式：配置驱动的适配器模式
- 通过 YAML 配置文件添加新模型提供商
- 无需修改核心代码即可扩展
- 支持 OpenAI 兼容 API

已支持的提供商：
- OpenAI (gpt-5.4)
- DeepSeek (deepseek-chat, deepseek-reasoner)
- Kimi (kimi-k2-turbo-preview, kimi-k2.5)

---

## 5. 数据模型设计

### 5.1 主数据库 (SQLite)

#### 5.1.1 用户表 (users)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT | 用户唯一标识（UUID） |
| nickname | TEXT | 用户昵称，用于登录 |
| password_hash | TEXT | 密码哈希（bcrypt加密） |
| role_name | TEXT | 角色名称 |
| preferences_json | TEXT | 用户偏好设置（JSON） |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |
| deleted_at | TIMESTAMP | 软删除时间 |

模型文件：[backend/models/user.py](file:///workspace/backend/models/user.py)

#### 5.1.2 角色卡表 (character_cards)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT | 角色卡唯一标识 |
| user_id | TEXT | 所属用户ID（外键） |
| role_overview | TEXT | 角色概述 |
| formal_name | TEXT | 正式名称 |
| nickname | TEXT | 昵称 |
| race_or_form | TEXT | 种族或形态 |
| gender | TEXT | 性别 |
| visual_age | TEXT | 视觉年龄 |
| actual_age | TEXT | 实际年龄 |
| location | TEXT | 所在位置 |
| appearance_desc | TEXT | 外貌描述 |
| core_personality | TEXT | 核心性格 |
| self_perception | TEXT | 自我认知 |
| attitude_to_user | TEXT | 对用户态度 |
| likes | TEXT | 喜好 |
| dislikes | TEXT | 厌恶 |
| tone_base | TEXT | 语气基调 |
| word_habits | TEXT | 用词习惯 |
| emotion_rules | TEXT | 情绪规则 |
| length_pref | TEXT | 长度偏好 |
| special_logic_list | TEXT | 特殊逻辑 |
| few_shot_examples | TEXT | 示例对话 |
| is_active | BOOLEAN | 是否激活 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

模型文件：[backend/models/character_card.py](file:///workspace/backend/models/character_card.py)

#### 5.1.3 对话表 (conversations)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT | 对话唯一标识 |
| user_id | TEXT | 所属用户ID（外键） |
| character_id | TEXT | 关联角色卡ID（外键） |
| title | TEXT | 对话标题 |
| is_active | BOOLEAN | 是否激活 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |
| deleted_at | TIMESTAMP | 软删除时间 |

模型文件：[backend/models/conversation.py](file:///workspace/backend/models/conversation.py)

#### 5.1.4 对话消息表 (conversation_logs)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 消息自增ID |
| conversation_id | TEXT | 所属对话ID（外键） |
| user_id | TEXT | 所属用户ID（外键） |
| role | TEXT | 角色（user/assistant） |
| content | TEXT | 消息内容 |
| timestamp | TIMESTAMP | 发送时间 |
| emotion_valence | REAL | 情感效价（-1~1） |
| emotion_arousal | REAL | 情感唤醒度（0~1） |
| embedding_id | TEXT | 向量嵌入ID |
| storage_status | TEXT | 存储状态 |
| storage_attempts | INTEGER | 存储尝试次数 |
| storage_error | TEXT | 存储错误信息 |
| stored_at | TIMESTAMP | 成功存储时间 |

模型文件：[backend/models/conversation_log.py](file:///workspace/backend/models/conversation_log.py)

#### 5.1.5 记忆总结表 (memory_summaries)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 自增ID |
| user_id | TEXT | 所属用户ID（外键） |
| conversation_id | TEXT | 关联对话ID（外键） |
| summary | TEXT | 总结内容 |
| turn_count | INTEGER | 对话轮数 |
| created_at | TIMESTAMP | 创建时间 |

模型文件：[backend/models/memory_summary.py](file:///workspace/backend/models/memory_summary.py)

#### 5.1.6 模型配置表 (model_configs)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT | 配置唯一标识 |
| account_id | TEXT | 所属用户ID（外键） |
| provider_id | TEXT | 提供商ID（外键） |
| name | TEXT | 配置名称 |
| base_url | TEXT | API 基础URL |
| api_key | TEXT | API 密钥（加密存储） |
| model_name | TEXT | 模型名称 |
| custom_model_name | TEXT | 自定义模型名称 |
| model_type | TEXT | 模型类型 |
| max_tokens | INTEGER | 最大Token数 |
| temperature | REAL | 温度参数 |
| is_enabled | BOOLEAN | 是否启用 |
| is_tested | BOOLEAN | 是否测试过 |
| test_status | TEXT | 测试状态 |
| last_test_at | TIMESTAMP | 最后测试时间 |
| last_test_message | TEXT | 测试消息 |
| edit_count | INTEGER | 编辑次数 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

模型文件：[backend/models/model_config.py](file:///workspace/backend/models/model_config.py)

#### 5.1.7 模型提供商表 (model_providers)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT | 提供商唯一标识 |
| name | TEXT | 提供商名称（内部标识） |
| display_name | TEXT | 显示名称 |
| description | TEXT | 描述 |
| created_at | TIMESTAMP | 创建时间 |

模型文件：[backend/models/model_provider.py](file:///workspace/backend/models/model_provider.py)

### 5.2 日志数据库 (独立 SQLite)

#### 5.2.1 系统日志表 (system_logs)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 自增ID |
| timestamp | TIMESTAMP | 日志时间 |
| level | TEXT | 日志级别 |
| event_type | TEXT | 事件类型 |
| trace_id | TEXT | 追踪ID |
| user_id | TEXT | 关联用户ID |
| session_id | TEXT | 会话ID |
| content | TEXT | 日志内容 |
| created_at | TIMESTAMP | 创建时间 |

模型文件：[backend/models/system_log.py](file:///workspace/backend/models/system_log.py)

#### 5.2.2 审计日志表 (audit_logs)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 自增ID |
| timestamp | TIMESTAMP | 操作时间 |
| user_id | TEXT | 操作用户ID |
| action | TEXT | 操作类型 |
| resource_type | TEXT | 资源类型 |
| resource_id | TEXT | 资源ID |
| result | TEXT | 操作结果 |
| client_ip | TEXT | 客户端IP |
| details | TEXT | 详细信息（JSON） |
| created_at | TIMESTAMP | 创建时间 |

模型文件：[backend/models/audit_log.py](file:///workspace/backend/models/audit_log.py)

#### 5.2.3 对话交互日志表 (dialogue_interaction_logs)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 自增ID |
| conversation_id | TEXT | 对话ID |
| user_id | TEXT | 用户ID |
| character_id | TEXT | 角色卡ID |
| request_detail | TEXT | 请求详情（JSON） |
| response_detail | TEXT | 响应详情（JSON） |
| start_time | TIMESTAMP | 开始时间 |
| end_time | TIMESTAMP | 结束时间 |
| duration_ms | INTEGER | 耗时（毫秒） |
| is_normal_end | INTEGER | 是否正常结束 |
| end_reason | TEXT | 结束原因 |
| user_emotion | TEXT | 用户情感 |
| assistant_emotion | TEXT | AI情感 |
| trace_id | TEXT | 追踪ID |
| created_at | TIMESTAMP | 创建时间 |

模型文件：[backend/models/dialogue_interaction_log.py](file:///workspace/backend/models/dialogue_interaction_log.py)

### 5.3 向量数据库 (ChromaDB)
- **Collection名称**：yumi_memories
- **存储内容**：对话内容的向量嵌入
- **元数据**：user_id, timestamp, importance_score, type 等

---

## 6. API接口

### 6.1 认证相关 (auth)
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/logout` - 用户登出
- `GET /api/auth/me` - 获取当前用户信息

### 6.2 聊天相关 (chat)
- `POST /api/chat` - 发送聊天消息（非流式）
- `GET /api/chat/stream` - 发送聊天消息（流式，SSE）
- `GET /api/chat/history` - 获取聊天历史
- `POST /api/chat/conversation` - 创建新对话
- `GET /api/chat/conversations` - 获取对话列表

### 6.3 角色卡相关 (character-cards)
- `GET /api/character-cards` - 获取角色卡列表
- `POST /api/character-cards` - 创建角色卡
- `GET /api/character-cards/{id}` - 获取角色卡详情
- `PUT /api/character-cards/{id}` - 更新角色卡
- `DELETE /api/character-cards/{id}` - 删除角色卡

### 6.4 模型相关 (models)
- `GET /api/models` - 获取模型配置列表
- `POST /api/models` - 创建模型配置
- `PUT /api/models/{id}` - 更新模型配置
- `DELETE /api/models/{id}` - 删除模型配置
- `POST /api/models/{id}/test` - 测试模型连接
- `GET /api/models/providers` - 获取模型提供商列表

### 6.5 记忆相关 (memory)
- `GET /api/memory/search` - 搜索记忆
- `POST /api/memory` - 存储记忆
- `DELETE /api/memory/{id}` - 删除记忆
- `GET /api/memory/stats` - 获取记忆统计
- `POST /api/memory/summarize` - 生成摘要

### 6.6 用户相关 (user)
- `GET /api/user` - 获取用户信息
- `PUT /api/user` - 更新用户信息
- `PUT /api/user/password` - 修改密码

### 6.7 设置相关 (settings)
- `GET /api/settings` - 获取系统设置
- `PUT /api/settings` - 更新系统设置

### 6.8 存储相关 (storage)
- `POST /api/storage/import` - 导入数据
- `GET /api/storage/export` - 导出数据
- `POST /api/storage/backup` - 创建备份
- `GET /api/storage/backups` - 获取备份列表

### 6.9 日志相关 (logs)
- `GET /api/logs/system` - 获取系统日志
- `GET /api/logs/audit` - 获取审计日志
- `GET /api/logs/dialogue` - 获取对话交互日志

### 6.10 缓存相关 (cache)
- `DELETE /api/cache` - 清除缓存
- `GET /api/cache/stats` - 获取缓存统计

详细 API 文档请参考：[docs/api.md](file:///workspace/docs/api.md)

---

## 7. 开发与部署

### 7.1 环境要求

| 组件 | 最低版本 |
|------|---------|
| Node.js | 20+ |
| Python | 3.10+ |
| Rust | 1.75+（Tauri开发） |

### 7.2 安装步骤

#### 7.2.1 克隆项目
```bash
git clone https://github.com/your-username/Yumi.git
cd Yumi
```

#### 7.2.2 安装前端依赖
```bash
npm install
```

#### 7.2.3 安装后端依赖
```bash
cd backend
pip install -r requirements.txt
```

### 7.3 开发运行

#### 7.3.1 前端开发
```bash
npm run dev
```
- 访问地址：http://localhost:1420
- API 代理：/api → http://127.0.0.1:8000

#### 7.3.2 后端开发
```bash
cd backend
python -m uvicorn main:app --reload
```
- API 文档：http://127.0.0.1:8000/docs
- 健康检查：http://127.0.0.1:8000/health

#### 7.3.3 Tauri 桌面应用（开发中）
```bash
npm run tauri dev
```

### 7.4 构建生产版本

#### 7.4.1 前端构建
```bash
npm run build
```

#### 7.4.2 后端部署
```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

#### 7.4.3 Tauri 构建
```bash
npm run tauri build
```

### 7.5 测试命令

#### 前端测试
```bash
# 运行测试
npm test

# 运行测试并生成覆盖率报告
npm run test:coverage

# 运行端到端测试
npm run test:e2e
```

#### 后端测试
```bash
cd backend
pytest tests/ -v
```

### 7.6 代码规范检查

#### 前端
```bash
# 代码检查
npm run lint:check

# 自动修复
npm run lint

# 格式化检查
npm run format:check

# 自动格式化
npm run format

# 类型检查
npm run typecheck
```

#### 后端
```bash
cd backend

# 代码检查
ruff check .

# 自动修复
ruff check --fix .

# 格式化检查
black --check .

# 自动格式化
black .

# 类型检查
mypy .
```

### 7.7 配置管理

#### 配置加载优先级
```
环境变量 > YAML 配置文件 > 默认值
```

#### 环境变量前缀
| 配置类 | 前缀 |
|--------|------|
| AppConfig | YUMI_ |
| ServerConfig | YUMI_SERVER_ |
| DatabaseConfig | YUMI_DB_ |
| VectorDBConfig | YUMI_VECTOR_ |
| LLMConfig | YUMI_LLM_ |
| MemoryConfig | YUMI_MEMORY_ |
| EmotionConfig | YUMI_EMOTION_ |
| LoggingConfig | YUMI_LOG_ |

#### 配置文件
- `config.yaml` - YAML 配置文件（可选）
- `.env` - 环境变量文件（可选）

---

## 8. 关键类与函数

### 8.1 后端关键类

#### 8.1.1 LLMService
**文件**：[backend/services/llm.py](file:///workspace/backend/services/llm.py)

**主要方法**：
- `chat(messages, temperature, max_tokens, ...)` - 非流式对话
- `stream_chat(messages, temperature, ...)` - 流式对话
- `test_connection(provider_id, base_url, api_key, model_name)` - 测试连接

#### 8.1.2 MemoryEngine
**文件**：[backend/services/memory.py](file:///workspace/backend/services/memory.py)

**主要方法**：
- `initialize()` - 初始化记忆引擎
- `store(user_id, content, metadata, skip_dedup)` - 存储记忆
- `search(query, top_k, user_id, apply_decay)` - 搜索记忆
- `get_recent(user_id, limit)` - 获取近期记忆
- `summarize_with_llm(user_id, llm_service, ...)` - LLM摘要
- `_calculate_importance(content)` - 计算重要性
- `_calculate_decay(timestamp_str, importance)` - 计算衰减因子

#### 8.1.3 User (Model)
**文件**：[backend/models/user.py](file:///workspace/backend/models/user.py)

**主要方法**：
- `is_deleted()` - 检查用户是否已删除

#### 8.1.4 PromptBuilder
**文件**：[backend/services/prompt_builder.py](file:///workspace/backend/services/prompt_builder.py)

**主要功能**：
- 整合角色卡信息
- 整合历史对话
- 整合检索到的记忆
- 整合情绪状态
- 构建完整的 LLM 提示

### 8.2 前端关键函数

#### 8.2.1 useChatStore
**文件**：[src/stores/chat.ts](file:///workspace/src/stores/chat.ts)

**主要方法**：
- `sendMessage(content, deepThinking)` - 发送消息
- `sendMessageStream(content)` - 发送流式消息
- `switchConversation(conversationId)` - 切换对话
- `startNewConversation(characterId)` - 开始新对话
- `loadHistory(limit)` - 加载历史消息
- `loadMoreMessages()` - 加载更多消息
- `stopStreaming()` - 停止流式响应
- `clearMessages()` - 清除消息

**主要状态**：
- `messages` - 消息列表
- `isLoading` - 加载状态
- `isStreaming` - 流式状态
- `currentConversationId` - 当前对话ID
- `streamingContent` - 流式内容

#### 8.2.2 API 客户端
**文件**：[src/api/chat.ts](file:///workspace/src/api/chat.ts)

**主要函数**：
- `sendMessage(request)` - 发送聊天请求
- `getHistory(userId, limit, offset, conversationId)` - 获取历史记录
- `createConversation(userId, characterId)` - 创建对话
- `getConversations(userId)` - 获取对话列表

---

## 附录

### 相关文档
- [README.md](file:///workspace/README.md) - 项目概览
- [docs/architecture.md](file:///workspace/docs/architecture.md) - 架构设计
- [docs/api.md](file:///workspace/docs/api.md) - API 文档
- [docs/database-design.md](file:///workspace/docs/database-design.md) - 数据库设计
- [docs/memory-engine.md](file:///workspace/docs/memory-engine.md) - 记忆引擎设计
- [docs/emotion-engine.md](file:///workspace/docs/emotion-engine.md) - 情绪引擎设计

### 许可证
本项目采用 MIT 许可证。
