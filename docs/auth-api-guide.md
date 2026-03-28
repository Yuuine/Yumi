# 认证系统 API 使用指南

## 概述

本系统提供了完整的账号注册和登录功能，使用 JWT (JSON Web Token) 进行身份验证。

## 功能特性

- 用户注册（昵称 + 密码）
- 用户登录
- Token 刷新
- 获取当前用户信息
- 密码加密存储（bcrypt）
- 昵称唯一性验证
- JWT 无状态认证

## 配置说明

### 环境变量

在 `.env` 文件或 `config.yaml` 中配置：

```yaml
jwt:
  secret_key: "your-secret-key-here"  # 生产环境请使用强密钥
  algorithm: "HS256"
  access_token_expire_minutes: 1440  # 24 小时
  refresh_token_expire_days: 30      # 30 天
```

环境变量格式：
- `YUMI_JWT_SECRET_KEY`
- `YUMI_JWT_ALGORITHM`
- `YUMI_JWT_ACCESS_TOKEN_EXPIRE_MINUTES`
- `YUMI_JWT_REFRESH_TOKEN_EXPIRE_DAYS`

## 依赖安装

确保已安装以下依赖：

```bash
pip install bcrypt>=4.1.0 pyjwt>=2.8.0
```

或在 `requirements.txt` 中添加：

```
bcrypt>=4.1.0
pyjwt>=2.8.0
```

## API 端点

### 1. 用户注册

注册新用户账号。

**Endpoint:** `POST /api/auth/register`

**请求体:**
```json
{
  "nickname": "测试用户",
  "password": "password123"
}
```

**响应 (200 OK):**
```json
{
  "userId": "550e8400-e29b-41d4-a716-446655440000",
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**错误响应 (400 Bad Request):**
```json
{
  "detail": "该昵称已被使用"
}
```

**昵称规则:**
- 长度：2-20 个字符
- 允许字符：字母、数字、下划线、中文
- 全局唯一

**密码规则:**
- 最小长度：6 个字符
- 最大长度：128 个字符

### 2. 用户登录

使用昵称和密码登录。

**Endpoint:** `POST /api/auth/login`

**请求体:**
```json
{
  "nickname": "测试用户",
  "password": "password123"
}
```

**响应 (200 OK):**
```json
{
  "userId": "550e8400-e29b-41d4-a716-446655440000",
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**错误响应 (401 Unauthorized):**
```json
{
  "detail": "昵称或密码错误"
}
```

### 3. 刷新 Token

使用刷新 Token 获取新的访问 Token 和刷新 Token。

**Endpoint:** `POST /api/auth/refresh`

**请求体:**
```json
{
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**响应 (200 OK):**
```json
{
  "userId": "550e8400-e29b-41d4-a716-446655440000",
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**错误响应 (401 Unauthorized):**
```json
{
  "detail": "无效的刷新令牌"
}
```

### 4. 获取当前用户信息

获取当前登录用户的信息。

**Endpoint:** `GET /api/auth/me`

**请求头:**
```
Authorization: Bearer <accessToken>
```

**响应 (200 OK):**
```json
{
  "userId": "550e8400-e29b-41d4-a716-446655440000",
  "nickname": "测试用户"
}
```

**错误响应 (401 Unauthorized):**
```json
{
  "detail": "无效的访问令牌"
}
```

## 使用示例

### JavaScript/TypeScript 示例

```typescript
// 注册
async function register(nickname: string, password: string) {
  const response = await fetch('/api/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ nickname, password })
  });
  return await response.json();
}

// 登录
async function login(nickname: string, password: string) {
  const response = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ nickname, password })
  });
  return await response.json();
}

// 存储 Token
function saveTokens(accessToken: string, refreshToken: string) {
  localStorage.setItem('accessToken', accessToken);
  localStorage.setItem('refreshToken', refreshToken);
}

// 刷新 Token
async function refreshAccessToken() {
  const refreshToken = localStorage.getItem('refreshToken');
  const response = await fetch('/api/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refreshToken })
  });

  if (response.ok) {
    const data = await response.json();
    saveTokens(data.accessToken, data.refreshToken);
    return data.accessToken;
  }
  return null;
}

// 带认证的 API 请求
async function fetchWithAuth(url: string, options: RequestInit = {}) {
  let accessToken = localStorage.getItem('accessToken');

  const response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${accessToken}`
    }
  });

  // Token 过期，尝试刷新
  if (response.status === 401) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      return fetch(url, {
        ...options,
        headers: {
          ...options.headers,
          'Authorization': `Bearer ${newToken}`
        }
      });
    }
  }

  return response;
}

// 使用示例
async function main() {
  // 注册
  const registerResult = await register('测试用户', 'password123');
  console.log('注册成功:', registerResult);
  saveTokens(registerResult.accessToken, registerResult.refreshToken);

  // 获取当前用户信息
  const userInfo = await fetchWithAuth('/api/auth/me');
  console.log('用户信息:', await userInfo.json());
}
```

### Python 示例

```python
import requests

BASE_URL = "http://localhost:8000/api"

def register(nickname: str, password: str):
    """注册用户"""
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={"nickname": nickname, "password": password}
    )
    response.raise_for_status()
    return response.json()

def login(nickname: str, password: str):
    """用户登录"""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"nickname": nickname, "password": password}
    )
    response.raise_for_status()
    return response.json()

def get_current_user(access_token: str):
    """获取当前用户信息"""
    response = requests.get(
        f"{BASE_URL}/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    response.raise_for_status()
    return response.json()

# 使用示例
if __name__ == "__main__":
    # 注册
    result = register("测试用户", "password123")
    user_id = result["userId"]
    access_token = result["accessToken"]
    refresh_token = result["refreshToken"]
    print(f"注册成功，用户ID: {user_id}")

    # 获取用户信息
    user = get_current_user(access_token)
    print(f"用户信息: {user}")
```

## 数据库迁移

首次启动时，数据库会自动创建或更新 `users` 表结构，添加以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| nickname | TEXT UNIQUE | 用户昵称（唯一） |
| password_hash | TEXT | 密码哈希 |
| id | TEXT PRIMARY KEY | 用户 UUID |

## 安全建议

1. **修改 JWT Secret Key**：生产环境必须使用强密钥
2. **使用 HTTPS**：生产环境必须使用 HTTPS 传输
3. **Token 存储**：在客户端安全存储 Token，避免 XSS 攻击
4. **密码强度**：建议前端增加密码强度检测
5. **限流保护**：建议添加登录和注册接口的限流机制

## 审计日志

所有注册和登录操作都会记录到 `audit_logs` 表中：

- `USER_REGISTER` - 用户注册
- `USER_LOGIN` - 用户登录

## 服务组件

### AuthService

综合认证服务，提供以下方法：

```python
from backend.services import auth_service

# 注册用户
user_id, access_token, refresh_token = await auth_service.register_user(
    nickname="测试用户",
    password="password123"
)

# 用户登录
result = await auth_service.login_user(
    nickname="测试用户",
    password="password123"
)

# 生成用户 UUID
user_id = auth_service.generate_user_id()
```

### 独立使用各服务组件

```python
from backend.services import (
    PasswordService,
    ValidatorService,
    JWTService,
    ValidationError
)

# 密码服务
hashed = PasswordService.hash_password("password123")
is_valid = PasswordService.verify_password("password123", hashed)

# 验证服务
is_valid, error = ValidatorService.validate_nickname("测试用户")
is_valid, error = ValidatorService.validate_password("password123")

# JWT 服务
jwt_service = JWTService()
access_token = jwt_service.generate_access_token("user-123", "测试用户")
refresh_token = jwt_service.generate_refresh_token("user-123")

# 验证 Token
user_id, nickname = jwt_service.verify_access_token(access_token)
user_id = jwt_service.verify_refresh_token(refresh_token)

# 刷新 Token
new_access, new_refresh = jwt_service.refresh_tokens(refresh_token, "测试用户")
```
