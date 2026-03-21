# Yumi 架构设计

## 目录

1. [系统总体架构](#1-系统总体架构)
2. [前端架构](#2-前端架构)
3. [后端架构](#3-后端架构)
4. [核心数据流](#4-核心数据流)
5. [核心模块概览](#5-核心模块概览)
6. [配置管理](#6-配置管理)
7. [开发工具](#7-开发工具)

---

## 文档导航

| 相关文档 | 说明 |
|---------|------|
| [项目 README](../README.md) | 项目概览、快速开始 |
| [API 文档](./api.md) | 完整的 RESTful API 接口 |
| [记忆引擎](./memory-engine.md) | 记忆引擎详细设计 |
| [情绪引擎](./emotion-engine.md) | 情绪引擎详细设计 |

---

## 1. 系统总体架构

```mermaid
graph TB
    %% 样式定义
    classDef user fill:#e3f2fd,stroke:#1976d2,stroke-width:2px;
    classDef frontend fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px;
    classDef desktop fill:#fff3e0,stroke:#f57c00,stroke-width:2px;
    classDef backend fill:#e8f5e9,stroke:#388e3c,stroke-width:2px;
    classDef data fill:#ffebee,stroke:#d32f2f,stroke-width:2px;
    classDef external fill:#eceff1,stroke:#607d8b,stroke-width:1px,stroke-dasharray:5 5;

    User["👤 用户"]:::user

    subgraph Frontend["前端表现层"]
        VueApp["Vue 3 应用"]:::frontend
        Pinia["Pinia 状态管理"]:::frontend
        ElementPlus["Element Plus UI"]:::frontend
    end

    subgraph Desktop["桌面应用层"]
        Tauri["Tauri 2.0 Runtime"]:::desktop
        IPC["IPC 通信"]:::desktop
    end

    subgraph Backend["后端服务层"]
        FastAPI["FastAPI"]:::backend
        Services["核心服务"]:::backend
        Core["基础设施"]:::backend
    end

    subgraph Data["数据持久层"]
        SQLite[(SQLite)]:::data
        ChromaDB[(ChromaDB)]:::data
        FS[(文件系统)]:::data
    end

    subgraph External["外部服务"]
        LLM["LLM API<br/>OpenAI/DeepSeek/Kimi/Ollama"]:::external
    end

    User --> VueApp
    VueApp --> Pinia
    VueApp --> ElementPlus
    Pinia --> IPC
    ElementPlus --> IPC
    IPC --> Tauri
    Tauri --> FastAPI
    FastAPI --> Services
    Services --> Core
    Services --> SQLite
    Services --> ChromaDB
    Core --> FS
    Services --> LLM
```

### 1.1 技术栈概览

| 层级 | 核心技术 | 说明 |
|------|---------|------|
| 前端 | Vue 3.4, TypeScript, Pinia, Vite | 响应式 UI、状态管理 |
| 桌面 | Tauri 2.0, Rust | 轻量级跨平台桌面 |
| 后端 | FastAPI 0.110, SQLAlchemy 2.0 | 异步 API、ORM |
| 数据库 | SQLite, ChromaDB 0.4.22 | 结构化数据 + 向量检索 |
| 外部 | OpenAI 兼容 API | 多模型提供商支持 |

> **详细文档**：
> - API 接口：[API 文档](./api.md)
> - 记忆引擎：[记忆引擎](./memory-engine.md)
> - 情绪引擎：[情绪引擎](./emotion-engine.md)

---

## 2. 前端架构

```mermaid
graph TB
    classDef page fill:#e3f2fd,stroke:#1976d2,stroke-width:2px;
    classDef component fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px;
    classDef store fill:#fff3e0,stroke:#f57c00,stroke-width:2px;
    classDef composable fill:#e8f5e9,stroke:#388e3c,stroke-width:2px;
    classDef util fill:#ffebee,stroke:#d32f2f,stroke-width:2px;
    classDef api fill:#eceff1,stroke:#607d8b,stroke-width:2px;

    Home["HomeView"]:::page

    subgraph Components["组件层"]
        App["App.vue"]:::component
        Sidebar["Sidebar"]:::component
        ChatContainer["ChatContainer"]:::component
        ChatInput["ChatInput"]:::component
        MessageList["MessageList"]:::component
        Settings["SettingsDialog"]:::component
    end

    subgraph Stores["状态管理层"]
        AccountStore["account.ts<br/>账户/加密"]:::store
        ChatStore["chat.ts<br/>对话/消息"]:::store
        AppStore["app.ts<br/>设置/UI"]:::store
        ModelsStore["models.ts<br/>模型配置"]:::store
    end

    subgraph Composables["组合式函数"]
        UseChat["use-chat"]:::composable
        UseStream["use-stream"]:::composable
        UseInit["use-init"]:::composable
        UseToast["use-toast"]:::composable
    end

    subgraph Utils["工具层"]
        Crypto["crypto-service"]:::util
        Storage["local-storage"]:::util
        Markdown["markdown"]:::util
    end

    subgraph Api["API 层"]
        ChatApi["api/chat"]:::api
        UserApi["api/user"]:::api
        ModelsApi["api/models"]:::api
    end

    Home --> App
    App --> Sidebar
    App --> ChatContainer
    ChatContainer --> ChatInput
    ChatContainer --> MessageList
    App --> Settings

    Components --> Stores
    Components --> Composables
    Stores --> Composables
    Composables --> Utils
    Composables --> Api
```

### 2.1 状态管理职责

| Store | 主要职责 |
|-------|---------|
| account.ts | 账户加密、密钥管理、角色卡、对话历史 |
| chat.ts | 当前对话、消息列表、生成状态 |
| app.ts | 应用设置、UI 状态 |
| models.ts | 模型列表、模型配置 |

---

## 3. 后端架构

```mermaid
graph TB
    classDef entry fill:#e3f2fd,stroke:#1976d2,stroke-width:2px;
    classDef router fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px;
    classDef service fill:#fff3e0,stroke:#f57c00,stroke-width:2px;
    classDef core fill:#e8f5e9,stroke:#388e3c,stroke-width:2px;
    classDef data fill:#ffebee,stroke:#d32f2f,stroke-width:2px;
    classDef external fill:#eceff1,stroke:#607d8b,stroke-width:1px,stroke-dasharray:5 5;

    Main["main.py<br/>FastAPI 入口"]:::entry

    subgraph Middleware["中间件层"]
        CORS["CORSMiddleware"]:::core
        Tracing["RequestTracing"]:::core
        SlowRequest["SlowRequestMonitor"]:::core
    end

    subgraph Routers["API 路由层"]
        ChatRouter["chat.py<br/>聊天 API"]:::router
        MemoryRouter["memory.py<br/>记忆 API"]:::router
        ModelsRouter["models.py<br/>模型 API"]:::router
        CardsRouter["character_cards.py<br/>角色卡 API"]:::router
        OtherRouters["...其他路由"]:::router
    end

    subgraph Services["业务服务层"]
        LLMService["llm.py<br/>LLM 服务"]:::service
        MemoryEngine["memory.py<br/>记忆引擎"]:::service
        EmotionEngine["emotion.py<br/>情绪引擎"]:::service
        PromptBuilder["prompt_builder.py<br/>提示构建器"]:::service
        ModelAdapters["model_adapters.py<br/>模型适配器"]:::service
        CacheService["cache_service.py<br/>缓存服务"]:::service
    end

    subgraph Core["核心基础设施"]
        Config["config.py<br/>配置管理"]:::core
        Logging["logging.py<br/>日志系统"]:::core
        Lifecycle["lifecycle.py<br/>生命周期"]:::core
    end

    subgraph Data["数据层"]
        SQLite[(SQLite)]:::data
        ChromaDB[(ChromaDB)]:::data
    end

    subgraph Providers["模型提供商"]
        OpenAI["providers/openai/"]:::data
        DeepSeek["providers/deepseek/"]:::data
        Kimi["providers/kimi/"]:::data
    end

    subgraph External["外部服务"]
        LLM["LLM API"]:::external
    end

    Main --> Middleware
    Main --> Routers

    ChatRouter --> LLMService
    ChatRouter --> MemoryEngine
    ChatRouter --> EmotionEngine
    ChatRouter --> PromptBuilder
    MemoryRouter --> MemoryEngine
    ModelsRouter --> ModelAdapters
    CardsRouter --> PromptBuilder

    LLMService --> ModelAdapters
    ModelAdapters --> Providers
    PromptBuilder --> MemoryEngine
    PromptBuilder --> EmotionEngine

    Services --> Core
    MemoryEngine --> ChromaDB
    Services --> SQLite
    LLMService --> LLM
```

### 3.1 核心服务说明

| 服务 | 职责 |
|------|------|
| LLMService | 调用外部 LLM API，处理流式响应 |
| MemoryEngine | 向量检索、记忆衰减、对话摘要 |
| EmotionEngine | 情绪分析、V-A 模型计算 |
| PromptBuilder | 整合多源信息，构建 LLM 上下文 |
| ModelAdapters | YAML 配置驱动的模型适配器 |

---

## 4. 核心数据流

### 4.1 聊天请求流程

```mermaid
sequenceDiagram
    participant User as 用户
    participant Frontend as 前端
    participant Backend as FastAPI
    participant Emotion as 情绪引擎
    participant Memory as 记忆引擎
    participant Prompt as 提示构建器
    participant LLM as LLM服务
    participant Adapter as 模型适配器
    participant External as 外部 LLM

    User->>Frontend: 输入消息
    Frontend->>Backend: POST /api/chat

    Backend->>Emotion: 分析情绪
    Backend->>Memory: 检索相关记忆

    Backend->>Prompt: 构建提示
    Note over Prompt: System + 8轮对话 + 6条RAG

    Backend->>LLM: 调用 LLM
    LLM->>Adapter: 适配模型
    Adapter->>External: HTTP 请求

    External-->>Adapter: 流式响应
    Adapter-->>LLM: 流式数据
    LLM-->>Backend: Server-Sent Events

    Backend->>Memory: 存储新消息
    Note over Memory: 检查是否需要摘要(70轮)

    Backend-->>Frontend: 流式数据
    Frontend-->>User: 打字机效果
```

---

## 5. 核心模块概览

### 5.1 模型适配器

**设计模式**：配置驱动的适配器模式

**扩展方式**：通过 YAML 配置文件添加新的模型提供商，无需修改核心代码。

**配置位置**：`backend/services/providers/`

### 5.2 记忆引擎

**核心功能**：向量检索、记忆衰减、对话摘要

> **详细设计**请参考 [记忆引擎](./memory-engine.md)。

### 5.3 情绪引擎

**模型**：效价-唤醒度（V-A）二维模型

> **详细设计**请参考 [情绪引擎](./emotion-engine.md)。

### 5.4 提示构建器

**职责**：整合多源信息，构建 LLM 输入上下文

---

## 6. 配置管理

### 6.1 配置加载优先级

```
环境变量 > YAML 配置文件 > 默认值
```

### 6.2 环境变量前缀

| 配置类 | 前缀 |
|--------|------|
| AppConfig | `YUMI_` |
| ServerConfig | `YUMI_SERVER_` |
| DatabaseConfig | `YUMI_DB_` |
| VectorDBConfig | `YUMI_VECTOR_` |
| LLMConfig | `YUMI_LLM_` |
| MemoryConfig | `YUMI_MEMORY_` |
| EmotionConfig | `YUMI_EMOTION_` |
| LoggingConfig | `YUMI_LOG_` |

### 6.3 配置文件

- `config.yaml` - YAML 配置文件（可选）
- `.env` - 环境变量文件（可选）

---

## 7. 开发工具

### 7.1 代码规范

| 层级 | 工具 |
|------|------|
| 前端 | ESLint, Prettier |
| 后端 | Ruff, Black, MyPy |

### 7.2 CI/CD

- **平台**：GitHub Actions
- **配置文件**：`.github/workflows/ci.yml`
- **前端检查**：lint + build
- **后端检查**：ruff + black --check
