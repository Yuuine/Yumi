# Yumi

<div align="center">
  <em>Yumi - AI 对话助手</em>
</div>

---

## 核心理念

- **隐私优先**：所有数据本地存储
- **情感智能**：记忆引擎 + 情绪分析

---

## 快速开始

### 环境要求

| 组件 | 最低版本 |
|------|---------|
| Node.js | 20+ |
| Python | 3.10+ |
| Rust | 1.75+ （⚠️：开发中，暂不支持） |

### 安装步骤

#### 1. 克隆项目
```bash
git clone https://github.com/your-username/Yumi.git
cd Yumi
```

#### 2. 安装前端依赖
```bash
npm install
```

#### 3. 安装后端依赖
```bash
cd backend
pip install -r requirements.txt
```

#### 4. 启动开发服务

**前端开发：**
```bash
npm run dev
```

**后端开发：**
```bash
cd backend
python -m uvicorn main:app --reload
```

**桌面应用（Tauri）：**（⚠️：开发中，暂不支持）
```bash
npm run tauri dev
```

---

## 功能特性

### 核心功能

| 功能 | 描述 | 状态 |
|------|------|------|
| 💬 智能对话 | 与 AI 角色进行自然流畅的对话 | ⚠️ 半完成 |
| 🧠 记忆引擎 | 基于向量检索的长期记忆系统 | ⚠️ 开发中 |
| 😊 情绪分析 | 基于 V-A 模型的情绪智能 | ⚠️ 开发中 |
| 🎭 角色卡系统 | 支持自定义 AI 角色性格 | ✅ 已完成 |
| 🔐 本地存储 | 所有数据加密存储在本地 | ✅ 已完成 |

---

## 📖 文档导航

| 文档 | 说明 |
|------|------|
| [架构设计](./docs/architecture.md) | 系统整体架构、模块划分、技术选型 |
| [API 文档](./docs/api.md) | 完整的 RESTful API 接口说明 |
| [记忆引擎](./docs/memory-engine.md) | 记忆引擎详细设计（艾宾浩斯遗忘曲线、向量检索等） |
| [情绪引擎](./docs/emotion-engine.md) | 情绪引擎详细设计（V-A 模型、双重情绪系统） |

---

## 🛠️ 技术栈（概览）

| 层级 | 核心技术 |
|------|---------|
| 前端 | Vue 3.4, TypeScript, Pinia, Vite |
| 桌面 | Tauri 2.0, Rust |
| 后端 | FastAPI 0.110, SQLAlchemy 2.0 |
| 数据库 | SQLite, ChromaDB 0.4.22 |
| 外部 | OpenAI 兼容 API |

> **详细技术栈与开发工具**请参考 [架构设计](./docs/architecture.md)。

---

## 更多帮助

- 详细开发指南请参考 [架构设计](./docs/architecture.md)
- 查看 [GitHub Issues](https://github.com/your-username/Yumi/issues)

---

## 致谢

- [Vue 3](https://cn.vuejs.org/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Tauri](https://tauri.app/)
- [ChromaDB](https://github.com/chroma-core/chroma)

---

## 许可证

本项目采用 MIT 许可证。
