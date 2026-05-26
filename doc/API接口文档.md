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


---

## 三、用户管理（/api/users）

用户 CRUD 与角色权限管理接口。需要 Bearer Token 认证，且要求 admin 角色。

### 3.1 获取用户列表

- **GET** `/api/users/list`
- **描述**：分页获取用户列表，支持关键词搜索和角色/状态筛选。需 admin 角色。
- **Content-Type**：application/json

| 参数 | 类型 | 位置 | 必填 | 说明 |
|------|------|------|------|------|
| Authorization | string | header | 是 | Bearer Token，格式 `Bearer <token>` |
| keyword | string\|null | body | 否 | 搜索关键词（匹配用户名、真实姓名、手机号） |
| role_id | int\|null | body | 否 | 角色 ID 筛选 |
| status | int\|null | body | 否 | 状态筛选：0=禁用，1=启用 |
| page | int | body | 是 | 页码，默认 1 |
| page_size | int | body | 是 | 每页数量，默认 10 |

**请求体示例**：

```json
{
  "keyword": "zhang",
  "role_id": null,
  "status": null,
  "page": 1,
  "page_size": 10
}
```

**响应格式**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "lists": [
      {
        "id": 1,
        "role_id": 1,
        "username": "zhangsan",
        "real_name": "张三",
        "phone": "13800138000",
        "dingtalk_id": "zhangsan@dingtalk",
        "status": 1,
        "last_login": "2026-05-25T10:30:00"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 10,
      "total": 1,
      "total_pages": 1
    }
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| lists[].id | int | 用户 ID |
| lists[].role_id | int | 角色 ID |
| lists[].username | string | 用户名 |
| lists[].real_name | string\|null | 真实姓名 |
| lists[].phone | string\|null | 手机号 |
| lists[].dingtalk_id | string\|null | 钉钉 ID |
| lists[].status | int | 状态：0=禁用，1=启用 |
| lists[].last_login | datetime\|null | 最后登录时间 |
| pagination.page | int | 当前页码 |
| pagination.page_size | int | 每页数量 |
| pagination.total | int | 总记录数 |
| pagination.total_pages | int | 总页数 |

### 3.2 添加用户

- **POST** `/api/users/add`
- **描述**：管理员添加新用户。需 admin 角色。
- **Content-Type**：application/json

| 参数 | 类型 | 位置 | 必填 | 说明 |
|------|------|------|------|------|
| Authorization | string | header | 是 | Bearer Token，格式 `Bearer <token>` |
| username | string | body | 是 | 用户名 |
| password | string | body | 否 | 密码，默认 `123456` |
| real_name | string\|null | body | 否 | 真实姓名 |
| phone | string\|null | body | 否 | 手机号，11 位 |
| role_id | int | body | 是 | 角色 ID |
| dingtalk_id | string\|null | body | 否 | 钉钉 ID，用于消息推送 |

**请求体示例**：

```json
{
  "username": "wangwu",
  "password": "Abc123456",
  "real_name": "王五",
  "phone": "13900139000",
  "role_id": 2,
  "dingtalk_id": "wangwu@dingtalk"
}
```

**响应格式**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 3,
    "username": "wangwu"
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 用户 ID |
| username | string | 用户名 |

**错误场景**：

| 错误码 | 场景 |
|--------|------|
| 1001 | 参数错误（缺少必填项） |
| 5001 | 用户名已存在 |

---

### 3.3 获取用户详情

- **GET** `/api/users/{id}`
- **描述**：根据用户 ID 获取用户详细信息。需 admin 角色。
- **Content-Type**：application/json

| 参数 | 类型 | 位置 | 必填 | 说明 |
|------|------|------|------|------|
| Authorization | string | header | 是 | Bearer Token，格式 `Bearer <token>` |
| id | int | path | 是 | 用户 ID |

**请求示例**：

```
GET /api/users/1
Authorization: Bearer <token>
```

**响应格式**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "username": "zhangsan",
    "role_id": 1,
    "real_name": "张三",
    "phone": "13800138000",
    "dingtalk_id": "zhangsan@dingtalk",
    "status": 1
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 用户 ID |
| username | string | 用户名 |
| role_id | int | 角色 ID |
| real_name | string\|null | 真实姓名 |
| phone | string\|null | 手机号 |
| dingtalk_id | string\|null | 钉钉 ID |
| status | int | 状态：0=禁用，1=启用 |

**错误场景**：

| 错误码 | 场景 |
|--------|------|
| 1002 | 数据不存在（用户不存在） |

---

### 3.4 更新用户

- **PUT** `/api/users/{id}`
- **描述**：更新用户信息。需 admin 角色。
- **Content-Type**：application/json

| 参数 | 类型 | 位置 | 必填 | 说明 |
|------|------|------|------|------|
| Authorization | string | header | 是 | Bearer Token，格式 `Bearer <token>` |
| id | int | path | 是 | 用户 ID |
| real_name | string\|null | body | 否 | 真实姓名 |
| phone | string\|null | body | 否 | 手机号，11 位 |
| role_id | int\|null | body | 否 | 角色 ID |
| dingtalk_id | string\|null | body | 否 | 钉钉 ID，用于消息推送 |
| status | int\|null | body | 否 | 状态：0=禁用，1=启用 |

**请求体示例**：

```json
{
  "real_name": "张三丰",
  "phone": "13800138001",
  "role_id": 2,
  "dingtalk_id": "zhangsanfeng@dingtalk",
  "status": 1
}
```

**响应格式**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "username": "zhangsan",
    "role_id": 2,
    "real_name": "张三丰",
    "phone": "13800138001",
    "dingtalk_id": "zhangsanfeng@dingtalk",
    "status": 1
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 用户 ID |
| username | string | 用户名 |
| role_id | int | 角色 ID |
| real_name | string\|null | 真实姓名 |
| phone | string\|null | 手机号 |
| dingtalk_id | string\|null | 钉钉 ID |
| status | int | 状态：0=禁用，1=启用 |

**错误场景**：

| 错误码 | 场景 |
|--------|------|
| 1002 | 数据不存在（用户不存在） |

---

## 四、角色管理（/api/roles）

角色列表查询。需要 Bearer Token 认证，且要求 admin 角色。

### 4.1 获取角色列表

- **GET** `/api/roles/list`
- **描述**：分页获取角色列表。需 admin 角色。
- **Content-Type**：application/json

| 参数 | 类型 | 位置 | 必填 | 说明 |
|------|------|------|------|------|
| Authorization | string | header | 是 | Bearer Token，格式 `Bearer <token>` |
| page | int | query | 否 | 页码，默认 1 |
| page_size | int | query | 否 | 每页数量，默认 10 |

**请求示例**：

```
GET /api/roles/list?page=1&page_size=10
Authorization: Bearer <token>
```

**响应格式**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "lists": [
      {
        "id": 1,
        "role_name": "管理员"
      },
      {
        "id": 2,
        "role_name": "监测员",
        "created_at": "2026-05-25T10:30:00"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 10,
      "total": 2,
      "total_pages": 1
    }
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| lists[].id | int | 角色 ID |
| lists[].role_name | string | 角色名称 |
| lists[].created_at | datetime\|null | 创建时间 |
| pagination.page | int | 当前页码 |
| pagination.page_size | int | 每页数量 |
| pagination.total | int | 总记录数 |
| pagination.total_pages | int | 总页数 |
