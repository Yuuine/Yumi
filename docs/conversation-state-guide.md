# 对话状态管理机制使用指南

## 概述

本系统提供了一个完整的对话状态管理机制，核心是维护 `messages` 列表字段，用于与大语言模型交互。

## 核心组件

### 1. Message（消息对象）

代表对话中的单条消息。

```python
from backend.services import Message, MessageRole

# 创建消息
msg = Message(
    role=MessageRole.USER,
    content="你好，我丢了一只猫",
    metadata={"source": "user_input"}
)

# 转换为 LLM 调用格式
llm_format = msg.to_dict()
# => {"role": "user", "content": "你好，我丢了一只猫"}

# 转换为完整格式（包含所有字段）
full_format = msg.to_full_dict()
# => {"role": "user", "content": "...", "timestamp": "...", "metadata": {...}}
```

### 2. ConversationState（对话状态）

管理单个对话实例的状态。

```python
from backend.services import ConversationState

# 创建对话状态（带系统提示词）
state = ConversationState(
    conversation_id="conv-123",
    system_prompt="你是夏洛克·福尔摩斯。你极其聪明，观察力敏锐...",
    max_history=50
)

# 添加用户消息
state.add_user_message("你好，我丢了一只猫")

# 添加助手消息
state.add_assistant_message("*头也不抬地拉着小提琴* 华生，别用这种琐事来浪费我的脑细胞...")

# 一次性添加一对消息
state.add_message_pair(
    "可是它脖子上有颗红宝石",
    "*猛地放下琴弓，眼神变得犀利* 红宝石？..."
)

# 获取用于 LLM 调用的 messages 列表
messages = state.messages
# => [
#      {"role": "system", "content": "..."},
#      {"role": "user", "content": "..."},
#      {"role": "assistant", "content": "..."},
#      ...
#    ]

# 获取最近 n 轮对话
recent_messages = state.get_last_n_turns(3)

# 清空历史（保留系统提示词）
state.clear_history(keep_system=True)

# 验证消息格式
is_valid, error = state.validate()
```

### 3. ConversationStateManager（状态管理器）

管理多个对话状态，提供缓存和持久化功能。

```python
from backend.services import conversation_state_manager

# 创建新状态
state = await conversation_state_manager.create_state(
    conversation_id="conv-456",
    user_id="user-123",
    system_prompt="你是夏洛克·福尔摩斯..."
)

# 获取或创建状态
state = await conversation_state_manager.get_or_create_state(
    conversation_id="conv-456",
    user_id="user-123",
    system_prompt="你是夏洛克·福尔摩斯..."
)

# 获取状态
state = await conversation_state_manager.get_state(
    conversation_id="conv-456",
    user_id="user-123"
)

# 添加用户消息（自动保存）
msg = await conversation_state_manager.add_user_message(
    conversation_id="conv-456",
    user_id="user-123",
    content="你好"
)

# 添加助手消息（自动保存）
msg = await conversation_state_manager.add_assistant_message(
    conversation_id="conv-456",
    user_id="user-123",
    content="你好！"
)

# 设置系统提示词
await conversation_state_manager.set_system_prompt(
    conversation_id="conv-456",
    user_id="user-123",
    content="新的系统提示词"
)

# 保存状态
await conversation_state_manager.save_state(user_id="user-123", state=state)

# 删除状态
await conversation_state_manager.delete_state(
    conversation_id="conv-456",
    user_id="user-123"
)

# 获取缓存统计
stats = conversation_state_manager.get_cache_stats()
# => {"cache_size": 10, "max_cache_size": 100, ...}
```

## 完整示例

```python
from backend.services import (
    ConversationState,
    ConversationStateManager,
    MessageRole,
    conversation_state_manager
)

# 1. 创建对话状态
state = ConversationState(
    conversation_id="sherlock-conv-001",
    system_prompt="""你是夏洛克·福尔摩斯。你极其聪明，观察力敏锐，但性格冷漠、傲慢。
你说话喜欢用演绎法推理，经常打断别人的废话。
称呼用户为'华生'或'委托人'。"""
)

# 2. 添加对话
state.add_message_pair(
    "你好，我丢了一只猫。",
    "*头也不抬地拉着小提琴* 华生，别用这种琐事来浪费我的脑细胞。除非那只猫是皇室丢失的，否则出门左转找苏格兰场。"
)

state.add_message_pair(
    "可是它脖子上有颗红宝石。",
    "*猛地放下琴弓，眼神变得犀利* 红宝石？*站起身快速踱步* 有趣……这就不是丢猫的问题了。告诉我，那只猫的品种和最后一次出现的地点。快！"
)

# 3. 获取用于 LLM 的 messages
messages = state.messages

# 4. 验证并调用 LLM
is_valid, error = state.validate()
if is_valid:
    # 调用你的 LLM 服务
    # response = llm_service.chat(messages=messages, ...)
    pass

# 5. 使用管理器持久化
await conversation_state_manager.create_state(
    conversation_id="sherlock-conv-001",
    user_id="user-001",
    system_prompt=state.system_prompt
)
# 添加消息会自动保存
await conversation_state_manager.add_user_message(
    "sherlock-conv-001",
    "user-001",
    "它是一只波斯猫，最后出现在贝克街221B附近。"
)
```

## 配置说明

在 `config.yaml` 或环境变量中配置：

```yaml
conversation_state:
  max_cache_size: 100          # 内存缓存最大对话状态数量
  default_max_history: 50       # 默认保留的最大历史消息数
```

环境变量：
- `YUMI_CONVERSATION_STATE_MAX_CACHE_SIZE`
- `YUMI_CONVERSATION_STATE_DEFAULT_MAX_HISTORY`

## 数据库表结构

### conversation_states

| 字段 | 类型 | 说明 |
|------|------|------|
| conversation_id | TEXT PRIMARY KEY | 对话 ID |
| user_id | TEXT NOT NULL | 用户 ID |
| state_json | TEXT NOT NULL | 序列化的状态 JSON |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |
