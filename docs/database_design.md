# Yumi 数据库表设计文档

## 概述

Yumi 系统采用 SQLite 作为数据库，支持主数据库和日志数据库分离，以提高性能和可维护性。

- **主数据库**: 存储核心业务数据
- **日志数据库**: 存储对话交互日志

---

## 一、主数据库表结构

### 1. users - 用户表

存储用户账号信息。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | TEXT | PRIMARY KEY | - | 用户唯一标识 |
| role_name | TEXT | - | 'Yumi' | 用户显示名称 |
| preferences_json | TEXT | - | NULL | 用户偏好设置（JSON格式） |
| created_at | TIMESTAMP | - | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | - | CURRENT_TIMESTAMP | 更新时间 |

**索引**: 无

**关联**:
- `id` → conversations.user_id
- `id` → character_cards.user_id
- `id` → model_configs.account_id

---

### 2. conversations - 对话表

存储对话实例信息。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | TEXT | PRIMARY KEY | - | 对话唯一标识 |
| user_id | TEXT | NOT NULL, FOREIGN KEY | - | 所属用户ID |
| character_id | TEXT | FOREIGN KEY | NULL | 关联角色卡ID |
| title | TEXT | - | NULL | 对话标题 |
| created_at | TIMESTAMP | - | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | - | CURRENT_TIMESTAMP | 更新时间 |
| is_active | BOOLEAN | - | 1 | 是否激活 |

**索引**:
- `idx_conversations_user` (user_id)
- `idx_conversations_active` (user_id, is_active)
- `idx_conversations_character` (character_id)

**关联**:
- `user_id` → users.id
- `character_id` → character_cards.id

---

### 3. conversation_logs - 对话消息日志表

存储对话中的每条消息记录。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | - | 自增主键 |
| conversation_id | TEXT | FOREIGN KEY | NULL | 所属对话ID |
| user_id | TEXT | NOT NULL, FOREIGN KEY | - | 用户ID |
| role | TEXT | NOT NULL | - | 角色（user/assistant） |
| content | TEXT | NOT NULL | - | 消息内容 |
| timestamp | TIMESTAMP | - | CURRENT_TIMESTAMP | 消息时间戳 |
| emotion_valence | REAL | - | NULL | 情绪效价值 |
| emotion_arousal | REAL | - | NULL | 情绪唤醒度 |
| embedding_id | TEXT | - | NULL | 向量存储ID |
| storage_status | TEXT | - | 'pending' | 存储状态 |
| storage_attempts | INTEGER | - | 0 | 存储尝试次数 |
| storage_error | TEXT | - | NULL | 存储错误信息 |
| stored_at | TIMESTAMP | - | NULL | 存储完成时间 |

**索引**:
- `idx_conversation_logs_user_time` (user_id, timestamp DESC)
- `idx_conversation_logs_conversation` (conversation_id)
- `idx_conversation_logs_storage_status` (storage_status)
- `idx_conversation_logs_storage_attempts` (storage_attempts)
- `idx_conversation_logs_stored_at` (stored_at)

**关联**:
- `user_id` → users.id
- `conversation_id` → conversations.id

---

### 4. memory_summaries - 记忆摘要表

存储对话记忆的摘要信息。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | - | 自增主键 |
| user_id | TEXT | NOT NULL, FOREIGN KEY | - | 用户ID |
| conversation_id | TEXT | FOREIGN KEY | NULL | 对话ID |
| summary | TEXT | NOT NULL | - | 摘要内容 |
| turn_count | INTEGER | - | 0 | 对话轮次 |
| created_at | TIMESTAMP | - | CURRENT_TIMESTAMP | 创建时间 |

**索引**:
- `idx_memory_summaries_user` (user_id)

**关联**:
- `user_id` → users.id
- `conversation_id` → conversations.id

---

### 5. character_cards - 角色卡表

存储AI角色卡配置信息。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | TEXT | PRIMARY KEY | - | 角色卡唯一标识 |
| user_id | TEXT | NOT NULL, FOREIGN KEY | - | 所属用户ID |
| conversation_id | TEXT | FOREIGN KEY | NULL | 关联对话ID |
| role_overview | TEXT | - | '' | 角色概述 |
| formal_name | TEXT | - | '' | 正式名称 |
| nickname | TEXT | - | '' | 昵称 |
| race_or_form | TEXT | - | '人类' | 种族/存在形式 |
| gender | TEXT | - | '中性' | 性别 |
| visual_age | TEXT | - | '' | 外表年龄 |
| actual_age | TEXT | - | '' | 实际年龄 |
| location | TEXT | - | '' | 存在地 |
| appearance_desc | TEXT | - | '' | 外貌描述 |
| core_personality | TEXT | - | '' | 核心性格 |
| self_perception | TEXT | - | '' | 自我认知 |
| attitude_to_user | TEXT | - | '' | 对用户态度 |
| likes | TEXT | - | '' | 喜好 |
| dislikes | TEXT | - | '' | 厌恶/雷点 |
| tone_base | TEXT | - | '' | 语气基调 |
| word_habits | TEXT | - | '' | 用词习惯 |
| emotion_rules | TEXT | - | '' | 情感表达规则 |
| length_pref | TEXT | - | '' | 对话长度偏好 |
| special_logic_list | TEXT | - | '' | 特殊情境反应逻辑 |
| few_shot_examples | TEXT | - | '' | 示例对话 |
| is_active | BOOLEAN | - | 1 | 是否激活 |
| created_at | TIMESTAMP | - | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | - | CURRENT_TIMESTAMP | 更新时间 |

**索引**:
- `idx_character_cards_user` (user_id)
- `idx_character_cards_conversation` (conversation_id)

**关联**:
- `user_id` → users.id
- `conversation_id` → conversations.id

---

### 6. model_providers - 模型提供商表

存储支持的AI模型提供商信息。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | TEXT | PRIMARY KEY | - | 提供商唯一标识 |
| name | TEXT | NOT NULL | - | 提供商名称 |
| display_name | TEXT | NOT NULL | - | 显示名称 |
| description | TEXT | - | NULL | 描述信息 |
| created_at | TIMESTAMP | - | CURRENT_TIMESTAMP | 创建时间 |

**索引**: 无

**预设数据**:
- deepseek - DeepSeek AI
- kimi - Moonshot AI
- custom - 自定义提供商

---

### 7. model_configs - 模型配置表

存储用户的模型API配置。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | TEXT | PRIMARY KEY | - | 配置唯一标识 |
| account_id | TEXT | NOT NULL, FOREIGN KEY | '' | 所属账号ID |
| provider_id | TEXT | NOT NULL, FOREIGN KEY | - | 提供商ID |
| name | TEXT | NOT NULL | - | 配置名称 |
| base_url | TEXT | NOT NULL | - | API基础URL |
| api_key | TEXT | - | NULL | API密钥 |
| model_name | TEXT | NOT NULL | - | 模型名称 |
| custom_model_name | TEXT | - | NULL | 自定义模型名称 |
| model_type | TEXT | - | 'text' | 模型类型 |
| max_tokens | INTEGER | - | 4096 | 最大Token数 |
| temperature | REAL | - | 0.85 | 温度参数 |
| is_enabled | BOOLEAN | - | 0 | 是否启用 |
| is_tested | BOOLEAN | - | 0 | 是否已测试 |
| test_status | TEXT | - | 'untested' | 测试状态 |
| last_test_at | TIMESTAMP | - | NULL | 最后测试时间 |
| last_test_message | TEXT | - | NULL | 最后测试消息 |
| edit_count | INTEGER | - | 0 | 编辑次数 |
| created_at | TIMESTAMP | - | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | - | CURRENT_TIMESTAMP | 更新时间 |

**索引**:
- `idx_model_configs_provider` (provider_id)
- `idx_model_configs_account` (account_id)
- `idx_model_configs_account_enabled` (account_id, is_enabled)
- `idx_model_configs_enabled` (is_enabled)
- `idx_model_configs_type` (model_type)

**关联**:
- `account_id` → users.id
- `provider_id` → model_providers.id

---

### 8. settings - 系统设置表

存储系统级配置。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| key | TEXT | PRIMARY KEY | - | 设置键名 |
| value | TEXT | NOT NULL | - | 设置值 |
| updated_at | TIMESTAMP | - | CURRENT_TIMESTAMP | 更新时间 |

**索引**: 无

---

### 9. system_logs - 系统日志表

存储系统运行日志。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | - | 自增主键 |
| timestamp | TEXT | NOT NULL | - | 日志时间戳 |
| level | TEXT | NOT NULL | - | 日志级别 |
| event_type | TEXT | NOT NULL | - | 事件类型 |
| trace_id | TEXT | - | NULL | 追踪ID |
| user_id | TEXT | - | NULL | 用户ID |
| session_id | TEXT | - | NULL | 会话ID |
| content | TEXT | NOT NULL | - | 日志内容 |
| created_at | TEXT | - | CURRENT_TIMESTAMP | 创建时间 |

**索引**:
- `idx_system_logs_timestamp` (timestamp)
- `idx_system_logs_level` (level)
- `idx_system_logs_event_type` (event_type)
- `idx_system_logs_trace_id` (trace_id)
- `idx_system_logs_user_id` (user_id)

---

### 10. audit_logs - 审计日志表

存储用户操作审计记录。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | - | 自增主键 |
| timestamp | TEXT | NOT NULL | - | 操作时间戳 |
| user_id | TEXT | - | NULL | 用户ID |
| action | TEXT | NOT NULL | - | 操作类型 |
| resource_type | TEXT | NOT NULL | - | 资源类型 |
| resource_id | TEXT | - | NULL | 资源ID |
| result | TEXT | NOT NULL | - | 操作结果 |
| client_ip | TEXT | - | NULL | 客户端IP |
| details | TEXT | - | NULL | 详细信息 |
| created_at | TEXT | - | CURRENT_TIMESTAMP | 创建时间 |

**索引**:
- `idx_audit_logs_timestamp` (timestamp)
- `idx_audit_logs_user_id` (user_id)
- `idx_audit_logs_action` (action)

---

## 二、日志数据库表结构

### dialogue_interaction_logs - 对话交互日志表

存储完整的对话交互记录，用于分析和调试。

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | - | 自增主键 |
| conversation_id | TEXT | - | NULL | 对话ID |
| user_id | TEXT | NOT NULL | - | 用户ID |
| character_id | TEXT | - | NULL | 角色卡ID |
| request_detail | TEXT | NOT NULL | - | 请求详情 |
| response_detail | TEXT | - | NULL | 响应详情 |
| start_time | TEXT | NOT NULL | - | 开始时间 |
| end_time | TEXT | - | NULL | 结束时间 |
| duration_ms | INTEGER | - | NULL | 耗时（毫秒） |
| is_normal_end | INTEGER | - | 1 | 是否正常结束 |
| end_reason | TEXT | - | '' | 结束原因 |
| user_emotion | TEXT | - | NULL | 用户情绪 |
| assistant_emotion | TEXT | - | NULL | AI情绪 |
| trace_id | TEXT | - | NULL | 追踪ID |
| created_at | TEXT | - | CURRENT_TIMESTAMP | 创建时间 |

**索引**:
- `idx_dialogue_logs_user_time` (user_id, start_time DESC)
- `idx_dialogue_logs_conversation` (conversation_id)
- `idx_dialogue_logs_character` (character_id)
- `idx_dialogue_logs_status` (is_normal_end)
- `idx_dialogue_logs_start_time` (start_time)
- `idx_dialogue_logs_trace_id` (trace_id)

---

## 三、ER 关系图

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   users     │     │  conversations   │     │ character_cards │
├─────────────┤     ├──────────────────┤     ├─────────────────┤
│ id (PK)     │◄────│ user_id (FK)     │     │ id (PK)         │
│ role_name   │     │ character_id(FK) │────►│ user_id (FK)    │
│ preferences │     │ id (PK)          │     │ role_overview   │
│ created_at  │     │ title            │     │ formal_name     │
│ updated_at  │     │ is_active        │     │ nickname        │
└─────────────┘     │ created_at       │     │ ...             │
      │             │ updated_at       │     └─────────────────┘
      │             └──────────────────┘             │
      │                    │                         │
      │                    │                         │
      ▼                    ▼                         │
┌──────────────────────────────────────┐            │
│         conversation_logs            │            │
├──────────────────────────────────────┤            │
│ id (PK)                              │            │
│ conversation_id (FK)                 │            │
│ user_id (FK)                         │            │
│ role                                 │            │
│ content                              │            │
│ timestamp                            │            │
│ emotion_valence / emotion_arousal    │            │
│ storage_status / storage_attempts    │            │
└──────────────────────────────────────┘            │
                                                     │
┌─────────────┐     ┌──────────────────┐            │
│model_providers│    │  model_configs   │            │
├─────────────┤     ├──────────────────┤            │
│ id (PK)     │◄────│ provider_id (FK) │            │
│ name        │     │ account_id (FK)  │◄───────────┘
│ display_name│     │ id (PK)          │
│ description │     │ name / base_url  │
└─────────────┘     │ api_key / model  │
                    │ is_enabled       │
                    └──────────────────┘
```

---

## 四、数据库配置

### SQLite PRAGMA 设置

```sql
PRAGMA journal_mode=WAL;        -- 写前日志模式，提高并发性能
PRAGMA synchronous=NORMAL;      -- 同步模式
PRAGMA cache_size=-64000;       -- 缓存大小 64MB
PRAGMA temp_store=MEMORY;       -- 临时存储在内存
PRAGMA mmap_size=268435456;     -- 内存映射大小 256MB
```

### 数据库文件位置

- 主数据库: `data/yumi.db`
- 日志数据库: `logs/yumi_logs.db`

---

## 五、数据流说明

### 1. 用户创建流程
1. 创建 `users` 记录
2. 创建默认 `character_cards` 记录
3. 创建默认 `conversations` 记录

### 2. 对话流程
1. 用户发送消息 → 创建 `conversation_logs` 记录（storage_status='pending'）
2. AI回复 → 创建 `conversation_logs` 记录
3. 异步存储到向量数据库 → 更新 `storage_status='completed'`
4. 更新 `conversations.updated_at`

### 3. 记忆摘要流程
1. 对话轮次达到阈值
2. 调用LLM生成摘要
3. 存储 `memory_summaries` 记录
4. 清理旧记忆向量

---

## 六、注意事项

1. **外键约束**: SQLite 默认不启用外键约束，需要在应用层保证数据一致性
2. **软删除**: 当前设计未实现软删除，删除操作会永久移除数据
3. **数据迁移**: 表结构变更通过 ALTER TABLE 实现，需要处理兼容性
4. **索引优化**: 已为常用查询场景创建索引，可根据实际使用情况调整
