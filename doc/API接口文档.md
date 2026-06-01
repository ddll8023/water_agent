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

| 错误码 | 说明                        |
| ------ | --------------------------- |
| 0      | 成功                        |
| 1001   | 参数错误                    |
| 1002   | 数据不存在                  |
| 2001   | 未登录 / 用户不存在或已禁用 |
| 2002   | 令牌过期                    |
| 2003   | 权限不足                    |
| 2004   | 令牌无效                    |
| 3001   | 文件格式不支持              |
| 3002   | 文件大小超过限制            |
| 4001   | 调用 AI 服务错误            |
| 5001   | 服务器内部错误              |
| 6001   | 密码错误                    |
| 7001   | 资源已存在                  |

- **Swagger 文档**：`http://localhost:3443/docs`

---

## 一、认证登录（/api/auth）

用户注册、登录与退出登录接口。

### 1.1 登录

- **POST** `/api/auth/login`
- **描述**：用户使用用户名和密码登录，返回访问令牌。

| 参数        | 类型         | 位置 | 必填 | 说明                  |
| ----------- | ------------ | ---- | ---- | --------------------- |
| username    | string       | body | 是   | 用户名                |
| password    | string       | body | 是   | 密码                  |
| phone       | string\|null | body | 否   | 手机号，11 位         |
| dingtalk_id | string\|null | body | 否   | 钉钉 ID，用于消息推送 |

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

| 字段         | 类型   | 说明                         |
| ------------ | ------ | ---------------------------- |
| access_token | string | JWT 访问令牌，有效期 24 小时 |
| username     | string | 用户名                       |

---

### 1.2 注册

- **POST** `/api/auth/register`
- **描述**：新用户注册。

| 参数     | 类型         | 位置 | 必填 | 说明          |
| -------- | ------------ | ---- | ---- | ------------- |
| username | string       | body | 是   | 用户名        |
| password | string       | body | 是   | 密码          |
| phone    | string\|null | body | 否   | 手机号，11 位 |

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

| 字段     | 类型   | 说明    |
| -------- | ------ | ------- |
| user_id  | int    | 用户 ID |
| username | string | 用户名  |

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

| 字段    | 类型   | 说明             |
| ------- | ------ | ---------------- |
| message | string | 退出登录提示信息 |

---

### 1.4 获取当前用户详情

- **GET** `/api/auth/me`
- **描述**：根据 Token 获取当前登录用户的详细信息。需要 Bearer Token 认证。
- **Content-Type**：application/json

| 参数          | 类型   | 位置   | 必填 | 说明                                  |
| ------------- | ------ | ------ | ---- | ------------------------------------- |
| Authorization | string | header | 是   | Bearer Token，格式 `Bearer <token>` |

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

| 字段        | 类型         | 说明                  |
| ----------- | ------------ | --------------------- |
| user_id     | int          | 用户 ID               |
| username    | string       | 用户名                |
| role        | string       | 用户角色名称          |
| phone       | string\|null | 手机号                |
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

| 字段    | 类型   | 说明                    |
| ------- | ------ | ----------------------- |
| status  | string | 服务状态，正常为 `ok` |
| version | string | 应用版本号              |

---

## 三、用户管理（/api/users）

用户 CRUD 与角色权限管理接口。需要 Bearer Token 认证，且要求 admin 角色。

### 3.1 获取用户列表

- **GET** `/api/users/list`
- **描述**：分页获取用户列表，支持关键词搜索和角色/状态筛选。需 admin 角色。
- **Content-Type**：application/json

| 参数          | 类型         | 位置   | 必填 | 说明                                       |
| ------------- | ------------ | ------ | ---- | ------------------------------------------ |
| Authorization | string       | header | 是   | Bearer Token，格式 `Bearer <token>`      |
| keyword       | string\|null | body   | 否   | 搜索关键词（匹配用户名、真实姓名、手机号） |
| role_id       | int\|null    | body   | 否   | 角色 ID 筛选                               |
| status        | int\|null    | body   | 否   | 状态筛选：0=禁用，1=启用                   |
| page          | int          | body   | 是   | 页码，默认 1                               |
| page_size     | int          | body   | 是   | 每页数量，默认 10                          |

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

| 字段                   | 类型           | 说明                 |
| ---------------------- | -------------- | -------------------- |
| lists[].id             | int            | 用户 ID              |
| lists[].role_id        | int            | 角色 ID              |
| lists[].username       | string         | 用户名               |
| lists[].real_name      | string\|null   | 真实姓名             |
| lists[].phone          | string\|null   | 手机号               |
| lists[].dingtalk_id    | string\|null   | 钉钉 ID              |
| lists[].status         | int            | 状态：0=禁用，1=启用 |
| lists[].last_login     | datetime\|null | 最后登录时间         |
| pagination.page        | int            | 当前页码             |
| pagination.page_size   | int            | 每页数量             |
| pagination.total       | int            | 总记录数             |
| pagination.total_pages | int            | 总页数               |

### 3.2 添加用户

- **POST** `/api/users/add`
- **描述**：管理员添加新用户。需 admin 角色。
- **Content-Type**：application/json

| 参数          | 类型         | 位置   | 必填 | 说明                                  |
| ------------- | ------------ | ------ | ---- | ------------------------------------- |
| Authorization | string       | header | 是   | Bearer Token，格式 `Bearer <token>` |
| username      | string       | body   | 是   | 用户名                                |
| password      | string       | body   | 否   | 密码，默认 `123456`                 |
| real_name     | string\|null | body   | 否   | 真实姓名                              |
| phone         | string\|null | body   | 否   | 手机号，11 位                         |
| role_id       | int          | body   | 是   | 角色 ID                               |
| dingtalk_id   | string\|null | body   | 否   | 钉钉 ID，用于消息推送                 |

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

| 字段     | 类型   | 说明    |
| -------- | ------ | ------- |
| id       | int    | 用户 ID |
| username | string | 用户名  |

**错误场景**：

| 错误码 | 场景                   |
| ------ | ---------------------- |
| 1001   | 参数错误（缺少必填项） |
| 5001   | 用户名已存在           |

---

### 3.3 获取用户详情

- **GET** `/api/users/{id}`
- **描述**：根据用户 ID 获取用户详细信息。需 admin 角色。
- **Content-Type**：application/json

| 参数          | 类型   | 位置   | 必填 | 说明                                  |
| ------------- | ------ | ------ | ---- | ------------------------------------- |
| Authorization | string | header | 是   | Bearer Token，格式 `Bearer <token>` |
| id            | int    | path   | 是   | 用户 ID                               |

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

| 字段        | 类型         | 说明                 |
| ----------- | ------------ | -------------------- |
| id          | int          | 用户 ID              |
| username    | string       | 用户名               |
| role_id     | int          | 角色 ID              |
| real_name   | string\|null | 真实姓名             |
| phone       | string\|null | 手机号               |
| dingtalk_id | string\|null | 钉钉 ID              |
| status      | int          | 状态：0=禁用，1=启用 |

**错误场景**：

| 错误码 | 场景                     |
| ------ | ------------------------ |
| 1002   | 数据不存在（用户不存在） |

---

### 3.4 更新用户

- **PUT** `/api/users/{id}`
- **描述**：更新用户信息。需 admin 角色。
- **Content-Type**：application/json

| 参数          | 类型         | 位置   | 必填 | 说明                                  |
| ------------- | ------------ | ------ | ---- | ------------------------------------- |
| Authorization | string       | header | 是   | Bearer Token，格式 `Bearer <token>` |
| id            | int          | path   | 是   | 用户 ID                               |
| real_name     | string\|null | body   | 否   | 真实姓名                              |
| phone         | string\|null | body   | 否   | 手机号，11 位                         |
| role_id       | int\|null    | body   | 否   | 角色 ID                               |
| dingtalk_id   | string\|null | body   | 否   | 钉钉 ID，用于消息推送                 |
| status        | int\|null    | body   | 否   | 状态：0=禁用，1=启用                  |

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

| 字段        | 类型         | 说明                 |
| ----------- | ------------ | -------------------- |
| id          | int          | 用户 ID              |
| username    | string       | 用户名               |
| role_id     | int          | 角色 ID              |
| real_name   | string\|null | 真实姓名             |
| phone       | string\|null | 手机号               |
| dingtalk_id | string\|null | 钉钉 ID              |
| status      | int          | 状态：0=禁用，1=启用 |

**错误场景**：

| 错误码 | 场景                     |
| ------ | ------------------------ |
| 1002   | 数据不存在（用户不存在） |

---

### 3.5 重置密码

- **POST** `/api/users/{id}/reset-password`
- **描述**：管理员重置指定用户的密码。需 admin 角色。
- **Content-Type**：application/json

| 参数          | 类型   | 位置   | 必填 | 说明                                  |
| ------------- | ------ | ------ | ---- | ------------------------------------- |
| Authorization | string | header | 是   | Bearer Token，格式 `Bearer <token>` |
| id            | int    | path   | 是   | 用户 ID                               |
| password      | string | body   | 是   | 新密码                                |

**请求示例**：

```
POST /api/users/1/reset-password
Authorization: Bearer <token>
Content-Type: application/json

{
  "password": "NewPass123"
}
```

**响应格式**：

```json
{
  "code": 0,
  "message": "success",
  "data": true
}
```

| 字段 | 类型 | 说明                      |
| ---- | ---- | ------------------------- |
| data | bool | 操作结果，成功为 `true` |

**错误场景**：

| 错误码 | 场景                     |
| ------ | ------------------------ |
| 1002   | 数据不存在（用户不存在） |

---

## 四、角色管理（/api/roles）

角色列表查询。需要 Bearer Token 认证，且要求 admin 角色。

### 4.1 获取角色列表

- **GET** `/api/roles/list`
- **描述**：分页获取角色列表。需 admin 角色。
- **Content-Type**：application/json

| 参数          | 类型   | 位置   | 必填 | 说明                                  |
| ------------- | ------ | ------ | ---- | ------------------------------------- |
| Authorization | string | header | 是   | Bearer Token，格式 `Bearer <token>` |
| page          | int    | query  | 否   | 页码，默认 1                          |
| page_size     | int    | query  | 否   | 每页数量，默认 10                     |

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
        "name": "管理员"
      },
      {
        "id": 2,
        "name": "监测员",
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

| 字段                   | 类型           | 说明     |
| ---------------------- | -------------- | -------- |
| lists[].id             | int            | 角色 ID  |
| lists[].name           | string         | 角色名称 |
| lists[].created_at     | datetime\|null | 创建时间 |
| pagination.page        | int            | 当前页码 |
| pagination.page_size   | int            | 每页数量 |
| pagination.total       | int            | 总记录数 |
| pagination.total_pages | int            | 总页数   |

### 4.2 添加角色

- **POST** `/api/roles/add`
- **描述**：管理员添加新角色。需 admin 角色。
- **Content-Type**：application/json

| 参数          | 类型          | 位置   | 必填 | 说明                                  |
| ------------- | ------------- | ------ | ---- | ------------------------------------- |
| Authorization | string        | header | 是   | Bearer Token，格式 `Bearer <token>` |
| name          | string        | body   | 是   | 角色名称                              |
| code          | string        | body   | 是   | 角色编码，需唯一                      |
| permissions   | array[string] | body   | 否   | 权限列表                              |

**请求体示例**：

```json
{
  "name": "分析员",
  "code": "analyst",
  "permissions": ["data:view", "report:export"]
}
```

**响应格式**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 4,
    "name": "分析员",
    "code": "analyst",
    "permissions": ["data:view", "report:export"],
    "created_at": "2026-05-26T10:30:00"
  }
}
```

| 字段        | 类型          | 说明     |
| ----------- | ------------- | -------- |
| id          | int           | 角色 ID  |
| name        | string        | 角色名称 |
| code        | string        | 角色编码 |
| permissions | array[string] | 权限列表 |
| created_at  | datetime      | 创建时间 |

**错误场景**：

| 错误码 | 场景                 |
| ------ | -------------------- |
| 5001   | 角色编码或名称已存在 |

### 4.3 获取角色详情

- **GET** `/api/roles/{id}`
- **描述**：根据角色 ID 获取角色详细信息。需 admin 角色。
- **Content-Type**：application/json

| 参数          | 类型   | 位置   | 必填 | 说明                                  |
| ------------- | ------ | ------ | ---- | ------------------------------------- |
| Authorization | string | header | 是   | Bearer Token，格式 `Bearer <token>` |
| id            | int    | path   | 是   | 角色 ID                               |

**请求示例**：

```
GET /api/roles/1
Authorization: Bearer <token>
```

**响应格式**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "name": "管理员",
    "code": "admin",
    "permissions": ["user:manage", "role:manage"],
    "created_at": "2026-05-25T10:30:00"
  }
}
```

| 字段        | 类型          | 说明     |
| ----------- | ------------- | -------- |
| id          | int           | 角色 ID  |
| name        | string        | 角色名称 |
| code        | string        | 角色编码 |
| permissions | array[string] | 权限列表 |
| created_at  | datetime      | 创建时间 |

**错误场景**：

| 错误码 | 场景                     |
| ------ | ------------------------ |
| 1002   | 数据不存在（角色不存在） |

### 4.4 更新角色

- **PUT** `/api/roles/update`
- **描述**：管理员更新角色信息。需 admin 角色。
- **Content-Type**：application/json

| 参数          | 类型          | 位置   | 必填 | 说明                                  |
| ------------- | ------------- | ------ | ---- | ------------------------------------- |
| Authorization | string        | header | 是   | Bearer Token，格式 `Bearer <token>` |
| id            | int           | body   | 是   | 角色 ID                               |
| name          | string        | body   | 否   | 角色名称                              |
| code          | string        | body   | 否   | 角色编码                              |
| permissions   | array[string] | body   | 否   | 权限列表                              |

**请求体示例**：

```json
{
  "id": 1,
  "name": "超级管理员",
  "code": "super_admin",
  "permissions": ["user:manage", "role:manage", "system:config"]
}
```

**响应格式**：

```json
{
  "code": 0,
  "message": "success",
  "data": true
}
```

| 字段 | 类型 | 说明                      |
| ---- | ---- | ------------------------- |
| data | bool | 操作结果，成功为 `true` |

**错误场景**：

| 错误码 | 场景                     |
| ------ | ------------------------ |
| 1002   | 数据不存在（角色不存在） |

### 4.5 删除角色

- **DELETE** `/api/roles/{id}`
- **描述**：管理员删除指定角色。需 admin 角色。
- **Content-Type**：application/json

| 参数          | 类型   | 位置   | 必填 | 说明                                  |
| ------------- | ------ | ------ | ---- | ------------------------------------- |
| Authorization | string | header | 是   | Bearer Token，格式 `Bearer <token>` |
| id            | int    | path   | 是   | 角色 ID                               |

**请求示例**：

```
DELETE /api/roles/3
Authorization: Bearer <token>
```

**响应格式**：

```json
{
  "code": 0,
  "message": "success",
  "data": true
}
```

| 字段 | 类型 | 说明                      |
| ---- | ---- | ------------------------- |
| data | bool | 操作结果，成功为 `true` |

**错误场景**：

| 错误码 | 场景                     |
| ------ | ------------------------ |
| 1002   | 数据不存在（角色不存在） |

---

## 五、水库管理（/api/reservoir）

水库列表查询与分页接口。需要 Bearer Token 认证，且要求 admin 角色。

### 5.1 获取水库列表

- **GET** `/api/reservoir/list`
- **描述**：分页获取水库列表，支持关键词搜索、所属流域、水质等级和状态筛选。需 admin 角色。
- **Content-Type**：application/json

| 参数          | 类型         | 位置   | 必填 | 说明                                  |
| ------------- | ------------ | ------ | ---- | ------------------------------------- |
| Authorization | string       | header | 是   | Bearer Token，格式 `Bearer <token>` |
| keyword       | string\|null | body   | 否   | 搜索关键词（匹配水库名称、水库编号）  |
| watershed     | string\|null | body   | 否   | 所属流域筛选                          |
| water_grade   | string\|null | body   | 否   | 水质等级筛选                          |
| status        | int\|null    | body   | 否   | 状态筛选：0=停用，1=启用              |
| page          | int          | body   | 是   | 页码，默认 1                          |
| page_size     | int          | body   | 是   | 每页数量，默认 10                     |

**请求体示例**：

```json
{
  "keyword": null,
  "watershed": null,
  "water_grade": null,
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
        "name": "三峡水库",
        "code": "SX-001",
        "capacity": "393000",
        "water_grade": "Ⅱ类",
        "watershed": "长江流域",
        "sort_order": 0,
        "created_at": "2026-05-25T10:30:00"
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

| 字段                   | 类型         | 说明                      |
| ---------------------- | ------------ | ------------------------- |
| lists[].id             | int          | 水库 ID                   |
| lists[].name           | string       | 水库名称                  |
| lists[].code           | string       | 水库编号                  |
| lists[].capacity       | string\|null | 库容（万 m³）            |
| lists[].water_grade    | string\|null | 水质等级（如 Ⅱ类、Ⅲ类） |
| lists[].watershed      | string\|null | 所属流域                  |
| lists[].sort_order     | int          | 排序值                    |
| lists[].created_at     | datetime     | 创建时间                  |
| pagination.page        | int          | 当前页码                  |
| pagination.page_size   | int          | 每页数量                  |
| pagination.total       | int          | 总记录数                  |
| pagination.total_pages | int          | 总页数                    |

### 5.2 创建水库

- **POST** `/api/reservoir/create`
- **描述**：管理员新增水库。需 admin 角色。
- **Content-Type**：application/json

| 参数          | 类型         | 位置   | 必填 | 说明                                  |
| ------------- | ------------ | ------ | ---- | ------------------------------------- |
| Authorization | string       | header | 是   | Bearer Token，格式 `Bearer <token>` |
| name          | string       | body   | 是   | 水库名称                              |
| code          | string       | body   | 是   | 水库编号                              |
| location      | string\|null | body   | 否   | 所在位置                              |
| longitude     | string\|null | body   | 否   | 经度                                  |
| latitude      | string\|null | body   | 否   | 纬度                                  |
| capacity      | string\|null | body   | 否   | 库容（万 m³）                        |
| water_grade   | string\|null | body   | 否   | 水质等级（如 Ⅱ类、Ⅲ类）             |
| watershed     | string\|null | body   | 否   | 所属流域                              |
| sort_order    | int          | body   | 否   | 排序值，默认 0                        |

**请求体示例**：

```json
{
  "name": "丹江口水库",
  "code": "DJK-001",
  "location": "湖北省丹江口市",
  "longitude": "111.508",
  "latitude": "32.558",
  "capacity": "290500",
  "water_grade": "Ⅱ类",
  "watershed": "长江流域",
  "sort_order": 1
}
```

**响应格式**：

```json
{
  "code": 0,
  "message": "success",
  "data": true
}
```

**错误场景**：

| 错误码 | 场景                         |
| ------ | ---------------------------- |
| 1001   | 参数错误（缺少必填项）       |
| 7001   | 资源已存在（水库编号已存在） |

### 5.3 获取水库详情

- **GET** `/api/reservoir/{id}`
- **描述**：根据水库 ID 获取水库详细信息。需 admin 角色。
- **Content-Type**：application/json

| 参数          | 类型   | 位置   | 必填 | 说明                                  |
| ------------- | ------ | ------ | ---- | ------------------------------------- |
| Authorization | string | header | 是   | Bearer Token，格式 `Bearer <token>` |
| id            | int    | path   | 是   | 水库 ID                               |

**请求示例**：

```
GET /api/reservoir/1
Authorization: Bearer <token>
```

**响应格式**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "name": "三峡水库",
    "code": "SX-001",
    "location": "湖北省宜昌市",
    "longitude": "111.508",
    "latitude": "30.824",
    "capacity": "393000",
    "water_grade": "Ⅱ类",
    "watershed": "长江流域",
    "sort_order": 0,
    "status": 1,
    "created_at": "2026-05-25T10:30:00"
  }
}
```

| 字段        | 类型         | 说明                 |
| ----------- | ------------ | -------------------- |
| id          | int          | 水库 ID              |
| name        | string       | 水库名称             |
| code        | string       | 水库编号             |
| location    | string\|null | 所在位置             |
| longitude   | string\|null | 经度                 |
| latitude    | string\|null | 纬度                 |
| capacity    | string\|null | 库容（万 m³）       |
| water_grade | string\|null | 水质等级             |
| watershed   | string\|null | 所属流域             |
| sort_order  | int          | 排序值               |
| status      | int          | 状态：0=停用，1=启用 |
| created_at  | datetime     | 创建时间             |

**错误场景**：

| 错误码 | 场景                     |
| ------ | ------------------------ |
| 1002   | 数据不存在（水库不存在） |

### 5.4 更新水库

- **PUT** `/api/reservoir/{id}`
- **描述**：管理员更新水库信息。需 admin 角色。
- **Content-Type**：application/json

| 参数          | 类型         | 位置   | 必填 | 说明                                  |
| ------------- | ------------ | ------ | ---- | ------------------------------------- |
| Authorization | string       | header | 是   | Bearer Token，格式 `Bearer <token>` |
| id            | int          | path   | 是   | 水库 ID                               |
| name          | string\|null | body   | 否   | 水库名称                              |
| code          | string\|null | body   | 否   | 水库编号                              |
| location      | string\|null | body   | 否   | 所在位置                              |
| longitude     | string\|null | body   | 否   | 经度                                  |
| latitude      | string\|null | body   | 否   | 纬度                                  |
| capacity      | string\|null | body   | 否   | 库容（万 m³）                        |
| water_grade   | string\|null | body   | 否   | 水质等级                              |
| watershed     | string\|null | body   | 否   | 所属流域                              |
| status        | int\|null    | body   | 否   | 状态：0=停用，1=启用                  |
| sort_order    | int\|null    | body   | 否   | 排序值                                |

**请求体示例**：

```json
{
  "name": "三峡水库",
  "code": "SX-001",
  "location": "湖北省宜昌市夷陵区",
  "longitude": "111.512",
  "latitude": "30.828",
  "capacity": "393000",
  "water_grade": "Ⅰ类",
  "watershed": "长江流域",
  "status": 1,
  "sort_order": 1
}
```

**响应格式**：

```json
{
  "code": 0,
  "message": "success",
  "data": true
}
```

**错误场景**：

| 错误码 | 场景                         |
| ------ | ---------------------------- |
| 1002   | 数据不存在（水库不存在）     |
| 7001   | 资源已存在（水库编码已存在） |

### 5.5 删除水库

- **DELETE** `/api/reservoir/{id}`
- **描述**：管理员删除指定水库。需 admin 角色。
- **Content-Type**：application/json

| 参数          | 类型   | 位置   | 必填 | 说明                                  |
| ------------- | ------ | ------ | ---- | ------------------------------------- |
| Authorization | string | header | 是   | Bearer Token，格式 `Bearer <token>` |
| id            | int    | path   | 是   | 水库 ID                               |

**请求示例**：

```
DELETE /api/reservoir/1
Authorization: Bearer <token>
```

**响应格式**：

```json
{
  "code": 0,
  "message": "success",
  "data": true
}
```

| 字段 | 类型 | 说明                      |
| ---- | ---- | ------------------------- |
| data | bool | 操作结果，成功为 `true` |

**错误场景**：

| 错误码 | 场景                     |
| ------ | ------------------------ |
| 1002   | 数据不存在（水库不存在） |

---

## 六、监测站点管理（/api/stations）

监测站点的创建、列表查询、详情获取与更新。需要 Bearer Token 认证，且要求 admin 角色。

### 6.1 创建监测站点

- **POST** `/api/stations/create`
- **描述**：管理员新增监测站点。需 admin 角色。
- **Content-Type**：application/json

| 参数           | 类型         | 位置   | 必填 | 说明                                                               |
| -------------- | ------------ | ------ | ---- | ------------------------------------------------------------------ |
| Authorization  | string       | header | 是   | Bearer Token，格式 `Bearer <token>`                              |
| reservoir_id   | int          | body   | 是   | 所属水库 ID                                                        |
| name           | string       | body   | 是   | 站点名称                                                           |
| code           | string       | body   | 是   | 站点编码                                                           |
| type           | string\|null | body   | 否   | 站点类型：`auto` 自动站 / `manual` 人工站 / `sensing` 遥感站 |
| longitude      | string\|null | body   | 否   | 经度                                                               |
| latitude       | string\|null | body   | 否   | 纬度                                                               |
| sampling_point | string\|null | body   | 否   | 采样点位描述                                                       |

**请求体示例**：

```json
{
  "reservoir_id": 1,
  "name": "三峡大坝上游自动监测站",
  "code": "SX-AUTO-001",
  "type": "auto",
  "longitude": "111.508",
  "latitude": "30.824",
  "sampling_point": "大坝上游500米处"
}
```

**响应格式**：

```json
{
  "code": 0,
  "message": "success",
  "data": true
}
```

| 字段 | 类型 | 说明                      |
| ---- | ---- | ------------------------- |
| data | bool | 操作结果，成功为 `true` |

**错误场景**：

| 错误码 | 场景                         |
| ------ | ---------------------------- |
| 1001   | 参数错误（缺少必填项）       |
| 7001   | 资源已存在（监测站点已存在） |

---

### 6.2 获取监测站点列表

- **GET** `/api/stations/list`
- **描述**：分页获取监测站点列表，支持关键词搜索、水库筛选、站点类型筛选。需 admin 角色。

| 参数          | 类型         | 位置   | 必填 | 说明                                                                   |
| ------------- | ------------ | ------ | ---- | ---------------------------------------------------------------------- |
| Authorization | string       | header | 是   | Bearer Token，格式 `Bearer <token>`                                  |
| reservoir_id  | int\|null    | query  | 否   | 所属水库 ID 筛选                                                       |
| keyword       | string\|null | query  | 否   | 搜索关键词（匹配站点名称）                                             |
| code          | string\|null | query  | 否   | 站点编码搜索                                                           |
| type          | string\|null | query  | 否   | 站点类型筛选：`auto` 自动站 / `manual` 人工站 / `sensing` 遥感站 |
| page          | int          | query  | 是   | 页码，默认 1                                                           |
| page_size     | int          | query  | 是   | 每页数量，默认 10                                                      |

**请求示例**：

```
GET /api/stations/list?keyword=三峡&page=1&page_size=10
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
        "reservoir_id": 1,
        "name": "三峡大坝上游自动监测站",
        "code": "SX-AUTO-001",
        "type": "auto",
        "sampling_point": "大坝上游500米处",
        "status": 1,
        "last_data_time": "2026-05-28T10:30:00"
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

| 字段                   | 类型           | 说明                                                               |
| ---------------------- | -------------- | ------------------------------------------------------------------ |
| lists[].id             | int            | 站点 ID                                                            |
| lists[].reservoir_id   | int            | 所属水库 ID                                                        |
| lists[].name           | string         | 站点名称                                                           |
| lists[].code           | string         | 站点编码                                                           |
| lists[].type           | string\|null   | 站点类型：`auto` 自动站 / `manual` 人工站 / `sensing` 遥感站 |
| lists[].longitude      | string\|null   | 经度                                                               |
| lists[].latitude       | string\|null   | 纬度                                                               |
| lists[].sampling_point | string\|null   | 采样点位描述                                                       |
| lists[].status         | int            | 运行状态：0=离线，1=在线                                           |
| lists[].last_data_time | datetime\|null | 最后数据时间                                                       |
| pagination.page        | int            | 当前页码                                                           |
| pagination.page_size   | int            | 每页数量                                                           |
| pagination.total       | int            | 总记录数                                                           |
| pagination.total_pages | int            | 总页数                                                             |

---

---

### 6.3 获取监测站点详情

- **GET** `/api/stations/{id}`
- **描述**：根据站点 ID 获取监测站点详细信息。需 admin 角色。

| 参数          | 类型   | 位置   | 必填 | 说明                                  |
| ------------- | ------ | ------ | ---- | ------------------------------------- |
| Authorization | string | header | 是   | Bearer Token，格式 `Bearer <token>` |
| id            | int    | path   | 是   | 监测站点 ID                           |

**请求示例**：

```
GET /api/stations/1
Authorization: Bearer <token>
```

**响应格式**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "reservoir_id": 1,
    "name": "三峡大坝上游自动监测站",
    "code": "SX-AUTO-001",
    "type": "auto",
    "longitude": "111.508",
    "latitude": "30.824",
    "sampling_point": "大坝上游500米处",
    "status": 1
  }
}
```

| 字段           | 类型         | 说明                     |
| -------------- | ------------ | ------------------------ |
| id             | int          | 站点 ID                  |
| reservoir_id   | int          | 所属水库 ID              |
| name           | string       | 站点名称                 |
| code           | string       | 站点编码                 |
| type           | string\|null | 站点类型                 |
| longitude      | string\|null | 经度                     |
| latitude       | string\|null | 纬度                     |
| sampling_point | string\|null | 采样点位描述             |
| status         | int          | 运行状态：0=离线，1=在线 |

**错误场景**：

| 错误码 | 场景                         |
| ------ | ---------------------------- |
| 1002   | 数据不存在（监测站点不存在） |

---

### 6.4 更新监测站点

- **PUT** `/api/stations/{id}`
- **描述**：管理员更新监测站点信息。需 admin 角色。
- **Content-Type**：application/json

| 参数           | 类型         | 位置   | 必填 | 说明                                                               |
| -------------- | ------------ | ------ | ---- | ------------------------------------------------------------------ |
| Authorization  | string       | header | 是   | Bearer Token，格式 `Bearer <token>`                              |
| id             | int          | path   | 是   | 监测站点 ID                                                        |
| reservoir_id   | int\|null    | body   | 否   | 所属水库 ID                                                        |
| name           | string\|null | body   | 否   | 站点名称                                                           |
| code           | string\|null | body   | 否   | 站点编码                                                           |
| type           | string\|null | body   | 否   | 站点类型：`auto` 自动站 / `manual` 人工站 / `sensing` 遥感站 |
| longitude      | string\|null | body   | 否   | 经度                                                               |
| latitude       | string\|null | body   | 否   | 纬度                                                               |
| sampling_point | string\|null | body   | 否   | 采样点位描述                                                       |
| status         | int\|null    | body   | 否   | 运行状态：0=离线，1=在线                                           |

**请求体示例**：

```json
{
  "name": "三峡大坝上游自动监测站",
  "code": "SX-AUTO-001",
  "type": "auto",
  "longitude": "111.512",
  "latitude": "30.828",
  "sampling_point": "大坝上游800米处",
  "status": 1
}
```

**响应格式**：

```json
{
  "code": 0,
  "message": "success",
  "data": true
}
```

| 字段 | 类型 | 说明                      |
| ---- | ---- | ------------------------- |
| data | bool | 操作结果，成功为 `true` |

**错误场景**：

| 错误码 | 场景                         |
| ------ | ---------------------------- |
| 1002   | 数据不存在（监测站点不存在） |
| 7001   | 资源已存在（站点编码已存在） |

---

### 6.5 删除监测站点

- **DELETE** `/api/stations/{id}`
- **描述**：管理员删除指定监测站点。需 admin 角色。
- **Content-Type**：application/json

| 参数          | 类型   | 位置   | 必填 | 说明                                  |
| ------------- | ------ | ------ | ---- | ------------------------------------- |
| Authorization | string | header | 是   | Bearer Token，格式 `Bearer <token>` |
| id            | int    | path   | 是   | 监测站点 ID                           |

**请求示例**：

```
DELETE /api/stations/1
Authorization: Bearer <token>
```

**响应格式**：

```json
{
  "code": 0,
  "message": "success",
  "data": true
}
```

| 字段 | 类型 | 说明                      |
| ---- | ---- | ------------------------- |
| data | bool | 操作结果，成功为 `true` |

**错误场景**：

| 错误码 | 场景                         |
| ------ | ---------------------------- |
| 1002   | 数据不存在（监测站点不存在） |

---

## 七、指标管理（/api/indicators）

监测指标 CRUD 接口。需要 Bearer Token 认证，且要求 admin 角色。

### 7.1 创建指标

- **POST** `/api/indicators/create`
- **描述**：管理员新增监测指标。需 admin 角色。
- **Content-Type**：application/json

| 参数               | 类型         | 位置   | 必填 | 说明                                  |
| ------------------ | ------------ | ------ | ---- | ------------------------------------- |
| Authorization      | string       | header | 是   | Bearer Token，格式 `Bearer <token>` |
| name               | string       | body   | 是   | 指标名称                              |
| code               | string       | body   | 是   | 指标编码                              |
| unit               | string\|null | body   | 否   | 单位，如 mg/L                         |
| category           | string\|null | body   | 否   | 分类：物理 / 化学 / 生物 / 综合       |
| standard_limit_i   | float\|null  | body   | 否   | Ⅰ类限值                              |
| standard_limit_ii  | float\|null  | body   | 否   | Ⅱ类限值                              |
| standard_limit_iii | float\|null  | body   | 否   | Ⅲ类限值                              |
| standard_limit_iv  | float\|null  | body   | 否   | Ⅳ类限值                              |
| standard_limit_v   | float\|null  | body   | 否   | Ⅴ类限值                              |
| is_core            | int\|null    | body   | 否   | 是否核心指标：0=否，1=是              |

**请求体示例**：

```json
{
  "name": "总磷",
  "code": "TP",
  "unit": "mg/L",
  "category": "化学",
  "standard_limit_i": 0.02,
  "standard_limit_ii": 0.1,
  "standard_limit_iii": 0.2,
  "standard_limit_iv": 0.3,
  "standard_limit_v": 0.4,
  "is_core": 1
}
```

**响应格式**：

```json
{
  "code": 0,
  "message": "success",
  "data": true
}
```

| 字段 | 类型 | 说明                      |
| ---- | ---- | ------------------------- |
| data | bool | 操作结果，成功为 `true` |

**错误场景**：

| 错误码 | 场景                             |
| ------ | -------------------------------- |
| 1001   | 参数错误（缺少必填项 name/code） |
| 7001   | 资源已存在（指标编码已存在）     |

---

### 7.2 获取指标列表

- **POST** `/api/indicators/list`
- **描述**：分页获取指标列表，支持名称、编码、分类和核心指标筛选。需 admin 角色。
- **Content-Type**：application/json

| 参数          | 类型         | 位置   | 必填 | 说明                                  |
| ------------- | ------------ | ------ | ---- | ------------------------------------- |
| Authorization | string       | header | 是   | Bearer Token，格式 `Bearer <token>` |
| name          | string\|null | body   | 否   | 指标名称（模糊搜索）                  |
| code          | string\|null | body   | 否   | 指标编码（模糊搜索）                  |
| category      | string\|null | body   | 否   | 分类筛选                              |
| is_core       | int\|null    | body   | 否   | 核心指标筛选：0=普通指标，1=核心指标  |
| page          | int          | body   | 是   | 页码，默认 1                          |
| page_size     | int          | body   | 是   | 每页数量，默认 10                     |

**请求体示例**：

```json
{
  "name": "总磷",
  "code": null,
  "category": null,
  "is_core": null,
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
        "name": "总磷",
        "code": "TP",
        "unit": "mg/L",
        "category": "化学",
        "standard_limit_i": 0.02,
        "standard_limit_ii": 0.1,
        "standard_limit_iii": 0.2,
        "standard_limit_iv": 0.3,
        "standard_limit_v": 0.4,
        "is_core": 1,
        "created_at": "2026-05-28T12:00:00"
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

| 字段                       | 类型         | 说明                     |
| -------------------------- | ------------ | ------------------------ |
| lists[].id                 | int          | 指标 ID                  |
| lists[].name               | string       | 指标名称                 |
| lists[].code               | string       | 指标编码                 |
| lists[].unit               | string\|null | 单位                     |
| lists[].category           | string\|null | 分类                     |
| lists[].standard_limit_i   | float\|null  | Ⅰ类限值                 |
| lists[].standard_limit_ii  | float\|null  | Ⅱ类限值                 |
| lists[].standard_limit_iii | float\|null  | Ⅲ类限值                 |
| lists[].standard_limit_iv  | float\|null  | Ⅳ类限值                 |
| lists[].standard_limit_v   | float\|null  | Ⅴ类限值                 |
| lists[].is_core            | int\|null    | 是否核心指标：0=否，1=是 |
| lists[].created_at         | datetime\|null | 创建时间               |
| pagination.page            | int          | 当前页码                 |
| pagination.page_size       | int          | 每页数量                 |
| pagination.total           | int          | 总记录数                 |
| pagination.total_pages     | int          | 总页数                   |

---

### 7.3 获取指标详情

- **GET** `/api/indicators/{id}`
- **描述**：根据指标 ID 获取指标详细信息。需 admin 角色。
- **Content-Type**：application/json

| 参数          | 类型   | 位置   | 必填 | 说明                                  |
| ------------- | ------ | ------ | ---- | ------------------------------------- |
| Authorization | string | header | 是   | Bearer Token，格式 `Bearer <token>` |
| id            | int    | path   | 是   | 指标 ID                               |

**请求示例**：

```
GET /api/indicators/1
Authorization: Bearer <token>
```

**响应格式**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "name": "总磷",
    "code": "TP",
    "unit": "mg/L",
    "category": "化学",
    "standard_limit_i": 0.02,
    "standard_limit_ii": 0.1,
    "standard_limit_iii": 0.2,
    "standard_limit_iv": 0.3,
    "standard_limit_v": 0.4,
    "is_core": 1
  }
}
```

| 字段               | 类型         | 说明                     |
| ------------------ | ------------ | ------------------------ |
| id                 | int          | 指标 ID                  |
| name               | string       | 指标名称                 |
| code               | string       | 指标编码                 |
| unit               | string\|null | 单位                     |
| category           | string\|null | 分类                     |
| standard_limit_i   | float\|null  | Ⅰ类限值                 |
| standard_limit_ii  | float\|null  | Ⅱ类限值                 |
| standard_limit_iii | float\|null  | Ⅲ类限值                 |
| standard_limit_iv  | float\|null  | Ⅳ类限值                 |
| standard_limit_v   | float\|null  | Ⅴ类限值                 |
| is_core            | int\|null    | 是否核心指标：0=否，1=是 |

**错误场景**：

| 错误码 | 场景                     |
| ------ | ------------------------ |
| 1002   | 数据不存在（指标不存在） |

---

### 7.4 更新指标

- **PUT** `/api/indicators/{id}`
- **描述**：更新指定指标的信息。需 admin 角色。
- **Content-Type**：application/json

| 参数              | 类型         | 位置   | 必填 | 说明                                  |
| ----------------- | ------------ | ------ | ---- | ------------------------------------- |
| Authorization     | string       | header | 是   | Bearer Token，格式 `Bearer <token>` |
| id                | int          | path   | 是   | 指标 ID                               |
| name              | string\|null | body   | 否   | 指标名称                              |
| code              | string\|null | body   | 否   | 指标编码                              |
| unit              | string\|null | body   | 否   | 单位                                  |
| category          | string\|null | body   | 否   | 分类                                  |
| standard_limit_i  | float\|null  | body   | 否   | Ⅰ类限值                              |
| standard_limit_ii | float\|null  | body   | 否   | Ⅱ类限值                              |
| standard_limit_iii| float\|null  | body   | 否   | Ⅲ类限值                              |
| standard_limit_iv | float\|null  | body   | 否   | Ⅳ类限值                              |
| standard_limit_v  | float\|null  | body   | 否   | Ⅴ类限值                              |
| is_core           | int\|null    | body   | 否   | 是否核心指标：0=否，1=是              |

**请求体示例**：

```json
{
  "name": "总磷（TP）",
  "unit": "mg/L",
  "category": "化学",
  "standard_limit_i": 0.02,
  "standard_limit_ii": 0.1,
  "standard_limit_iii": 0.2,
  "standard_limit_iv": 0.3,
  "standard_limit_v": 0.4,
  "is_core": 1
}
```

**响应格式**：

```json
{
  "code": 0,
  "message": "success",
  "data": true
}
```

| 字段 | 类型 | 说明                      |
| ---- | ---- | ------------------------- |
| data | bool | 操作结果，成功为 `true` |

**错误场景**：

| 错误码 | 场景                     |
| ------ | ------------------------ |
| 1002   | 数据不存在（指标不存在） |
| 7001   | 资源已存在（指标编码已存在） |

### 7.5 删除指标

- **DELETE** `/api/indicators/{id}`
- **描述**：删除指定指标。需 admin 角色。
- **Content-Type**：application/json

| 参数          | 类型   | 位置   | 必填 | 说明                                  |
| ------------- | ------ | ------ | ---- | ------------------------------------- |
| Authorization | string | header | 是   | Bearer Token，格式 `Bearer <token>` |
| id            | int    | path   | 是   | 指标 ID                               |

**请求示例**：

```
DELETE /api/indicators/1
Authorization: Bearer <token>
```

**响应格式**：

```json
{
  "code": 0,
  "message": "success",
  "data": true
}
```

| 字段 | 类型 | 说明                      |
| ---- | ---- | ------------------------- |
| data | bool | 操作结果，成功为 `true` |

**错误场景**：

| 错误码 | 场景                     |
| ------ | ------------------------ |
| 1002   | 数据不存在（指标不存在） |

---

## 八、监测记录管理（/api/monitoring）

监测记录查询接口。需要 Bearer Token 认证，admin 与 user 角色均可访问。

### 8.1 获取监测记录列表

- **GET** `/api/monitoring/records`
- **描述**：分页获取监测记录列表，支持按水库、站点、指标、时间范围、数据质量标志筛选，按监测时间倒序。需 admin 或 user 角色。
- **Content-Type**：application/json

| 参数           | 类型            | 位置   | 必填 | 说明                                                            |
| -------------- | --------------- | ------ | ---- | --------------------------------------------------------------- |
| Authorization  | string          | header | 是   | Bearer Token，格式 `Bearer <token>`                          |
| page           | int             | query  | 否   | 页码，默认 1                                                    |
| page_size      | int             | query  | 否   | 每页记录数，默认 10，最大 100                                   |
| reservoir_id   | int\|null       | query  | 否   | 水库 ID 筛选                                                    |
| station_id     | int\|null       | query  | 否   | 站点 ID 筛选                                                    |
| indicator_id   | int\|null       | query  | 否   | 指标 ID 筛选                                                    |
| start_time     | datetime\|null  | query  | 否   | 开始时间，格式 `YYYY-MM-DD HH:MM:SS`                        |
| end_time       | datetime\|null  | query  | 否   | 结束时间，格式 `YYYY-MM-DD HH:MM:SS`                        |
| quality_flag   | int\|null       | query  | 否   | 数据质量标志：0 可疑，1 正常，2 无效                            |

**请求示例**：

```
GET /api/monitoring/records?page=1&page_size=10&reservoir_id=1&quality_flag=1
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
        "id": 1024,
        "reservoir_id": 1,
        "station_id": 1,
        "indicator_id": 3,
        "value": 0.082,
        "record_time": "2026-06-01 10:30:00"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 10,
      "total": 128,
      "total_pages": 13
    }
  }
}
```

| 字段                   | 类型         | 说明                                            |
| ---------------------- | ------------ | ----------------------------------------------- |
| lists[].id             | int          | 监测记录 ID                                     |
| lists[].reservoir_id   | int          | 水库 ID                                         |
| lists[].station_id     | int          | 站点 ID                                         |
| lists[].indicator_id   | int          | 指标 ID                                         |
| lists[].value          | float        | 监测值                                          |
| lists[].record_time    | datetime     | 监测时间，格式 `YYYY-MM-DD HH:MM:SS`         |
| pagination.page        | int          | 当前页码                                        |
| pagination.page_size   | int          | 每页数量                                        |
| pagination.total       | int          | 总记录数                                        |
| pagination.total_pages | int          | 总页数                                          |

### 8.2 获取最新监测记录

- **GET** `/api/monitoring/last`
- **描述**：根据站点 ID 和指标 ID 获取最新一条监测记录。需 admin 或 user 角色。
- **Content-Type**：application/json

| 参数          | 类型   | 位置   | 必填 | 说明                                  |
| ------------- | ------ | ------ | ---- | ------------------------------------- |
| Authorization | string | header | 是   | Bearer Token，格式 `Bearer <token>` |
| reservoir_id  | int    | query  | 是   | 水库 ID                               |
| station_id    | int    | query  | 是   | 站点 ID                               |
| indicator_id  | int    | query  | 是   | 指标 ID                               |

**请求示例**：

```
GET /api/monitoring/last?reservoir_id=1&station_id=1&indicator_id=3
Authorization: Bearer <token>
```

**响应格式**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1024,
    "reservoir_id": 1,
    "station_id": 1,
    "indicator_id": 3,
    "value": 0.082,
    "quality_flag": 1,
    "record_time": "2026-06-01 10:30:00"
  }
}
```

| 字段           | 类型     | 说明                                          |
| -------------- | -------- | --------------------------------------------- |
| id             | int      | 监测记录 ID                                   |
| reservoir_id   | int      | 水库 ID                                       |
| station_id     | int      | 站点 ID                                       |
| indicator_id   | int      | 指标 ID                                       |
| value          | float    | 监测值                                        |
| quality_flag   | int      | 数据质量标志：0 可疑，1 正常，2 无效          |
| record_time    | datetime | 监测时间，格式 `YYYY-MM-DD HH:MM:SS`       |

**错误场景**：

| 错误码 | 场景                       |
| ------ | -------------------------- |
| 1002   | 数据不存在（监测记录不存在） |

### 8.3 获取监测记录趋势

- **GET** `/api/monitoring/trend`
- **描述**：根据水库 ID、指标 ID、时间范围获取监测记录趋势数据，按监测时间倒序排列。需 admin 或 user 角色。
- **Content-Type**：application/json

| 参数          | 类型     | 位置   | 必填 | 说明                                           |
| ------------- | -------- | ------ | ---- | ---------------------------------------------- |
| Authorization | string   | header | 是   | Bearer Token，格式 `Bearer <token>`          |
| reservoir_id  | int      | query  | 是   | 水库 ID                                        |
| indicator_id  | int      | query  | 是   | 指标 ID                                        |
| start_time    | datetime | query  | 是   | 开始时间，格式 `YYYY-MM-DD HH:MM:SS`       |
| end_time      | datetime | query  | 是   | 结束时间，格式 `YYYY-MM-DD HH:MM:SS`       |

**请求示例**：

```
GET /api/monitoring/trend?reservoir_id=1&indicator_id=3&start_time=2026-06-01 00:00:00&end_time=2026-06-01 23:59:59
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
        "reservoir_id": 1,
        "indicator_id": 3,
        "record_time": "2026-06-01 08:00:00",
        "value": 0.082
      },
      {
        "reservoir_id": 1,
        "indicator_id": 3,
        "record_time": "2026-06-01 07:00:00",
        "value": 0.079
      }
    ],
    "total": 24
  }
}
```

| 字段                 | 类型     | 说明                                          |
| -------------------- | -------- | --------------------------------------------- |
| lists[].reservoir_id | int      | 水库 ID                                       |
| lists[].indicator_id | int      | 指标 ID                                       |
| lists[].record_time  | datetime | 监测时间，格式 `YYYY-MM-DD HH:MM:SS`       |
| lists[].value        | float    | 监测值                                        |
| total                | int      | 总记录数                                      |
