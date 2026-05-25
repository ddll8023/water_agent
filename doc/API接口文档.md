# API 接口文档

## 概述

- **基础 URL**：`http://localhost:3443`
- **认证方式**：Bearer Token，在请求头中携带 `Authorization: Bearer <token>`
- **统一响应格式**：所有接口返回 `ApiResponse` 结构体：

```json
{
  "code": 0,
  "message": "success",
  "data": { ... }
}
```

- **错误响应**：

```json
{
  "code": 1001,
  "message": "参数错误",
  "data": null
}
```

- **错误码表**：

| 错误码 | 说明 |
|--------|------|
| 0 | 成功 |
| 1001 | 参数错误 |
| 1002 | 数据不存在 |
| 2001 | 未登录 / 用户不存在或已禁用 |
| 2002 | 令牌过期 |
| 2003 | 权限不足 |
| 2004 | 令牌无效 |
| 3001 | 文件格式不支持 |
| 3002 | 文件大小超过限制 |
| 4001 | 调用 AI 服务错误 |
| 5001 | 服务器内部错误 |
| 6001 | 密码错误 |

- **Swagger 文档**：`http://localhost:3443/docs`

---

## 一、认证登录（/api/auth）

用户注册、登录与退出登录接口。

### 1.1 登录

- **POST** `/api/auth/login`
- **描述**：用户使用用户名和密码登录，返回访问令牌。

| 参数 | 类型 | 位置 | 必填 | 说明 |
|------|------|------|------|------|
| username | string | body | 是 | 用户名 |
| password | string | body | 是 | 密码 |
| phone | string\|null | body | 否 | 手机号，11 位 |
| dingtalk_id | string\|null | body | 否 | 钉钉 ID，用于消息推送 |

**请求体示例**：

```json
{
  "username": "zhangsan",
  "password": "Abc123456"
}
```

**响应格式**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "username": "zhangsan"
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| access_token | string | JWT 访问令牌，有效期 24 小时 |
| username | string | 用户名 |

---

### 1.2 注册

- **POST** `/api/auth/register`
- **描述**：新用户注册。

| 参数 | 类型 | 位置 | 必填 | 说明 |
|------|------|------|------|------|
| username | string | body | 是 | 用户名 |
| password | string | body | 是 | 密码 |
| phone | string\|null | body | 否 | 手机号，11 位 |

**请求体示例**：

```json
{
  "username": "lisi",
  "password": "Def789012"
}
```

**响应格式**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "user_id": 2,
    "username": "lisi"
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | int | 用户 ID |
| username | string | 用户名 |

---

### 1.3 退出登录

- **POST** `/api/auth/logout`
- **描述**：退出登录，前端清除 Token，后端返回成功消息。无请求体。

**响应格式**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "message": "退出登录成功"
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| message | string | 退出登录提示信息 |

---

### 1.4 获取当前用户详情

- **GET** `/api/auth/me`
- **描述**：根据 Token 获取当前登录用户的详细信息。需要 Bearer Token 认证。
- **Content-Type**：application/json

| 参数 | 类型 | 位置 | 必填 | 说明 |
|------|------|------|------|------|
| Authorization | string | header | 是 | Bearer Token，格式 `Bearer <token>` |

**响应格式**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "user_id": 1,
    "username": "zhangsan",
    "role": "监测员",
    "phone": "13800138000",
    "dingtalk_id": "zhangsan@dingtalk"
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | int | 用户 ID |
| username | string | 用户名 |
| role | string | 用户角色名称 |
| phone | string\|null | 手机号 |
| dingtalk_id | string\|null | 钉钉 ID，用于消息推送 |

---

## 二、系统与健康检查

### 2.1 健康检查

- **GET** `/health`
- **描述**：检测服务运行状态。无需认证，无请求参数。

**响应格式**：

```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| status | string | 服务状态，正常为 `ok` |
| version | string | 应用版本号 |
