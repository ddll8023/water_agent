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
| standard_limit_i_lower | float\|null  | body   | 否   | Ⅰ类下限值
| standard_limit_i_upper | float\|null  | body   | 否   | Ⅰ类上限值                              |
| standard_limit_ii_lower | float\|null  | body   | 否   | Ⅱ类下限值
| standard_limit_ii_upper | float\|null  | body   | 否   | Ⅱ类上限值                              |
| standard_limit_iii_lower | float\|null  | body   | 否   | Ⅲ类下限值
| standard_limit_iii_upper | float\|null  | body   | 否   | Ⅲ类上限值                              |
| standard_limit_iv_lower | float\|null  | body   | 否   | Ⅳ类下限值
| standard_limit_iv_upper | float\|null  | body   | 否   | Ⅳ类上限值                              |
| standard_limit_v_lower | float\|null  | body   | 否   | Ⅴ类下限值
| standard_limit_v_upper | float\|null  | body   | 否   | Ⅴ类上限值                              |
| is_core            | int\|null    | body   | 否   | 是否核心指标：0=否，1=是              |

**请求体示例**：

```json
{
  "name": "总磷",
  "code": "TP",
  "unit": "mg/L",
  "category": "化学",
  "standard_limit_i_lower": null,
  "standard_limit_i_upper": 0.02,
  "standard_limit_ii_lower": null,
  "standard_limit_ii_upper": 0.1,
  "standard_limit_iii_lower": null,
  "standard_limit_iii_upper": 0.2,
  "standard_limit_iv_lower": null,
  "standard_limit_iv_upper": 0.3,
  "standard_limit_v_lower": null,
  "standard_limit_v_upper": 0.4,
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
        "standard_limit_i_lower": null,
  "standard_limit_i_upper": 0.02,
        "standard_limit_ii_lower": null,
  "standard_limit_ii_upper": 0.1,
        "standard_limit_iii_lower": null,
  "standard_limit_iii_upper": 0.2,
        "standard_limit_iv_lower": null,
  "standard_limit_iv_upper": 0.3,
        "standard_limit_v_lower": null,
  "standard_limit_v_upper": 0.4,
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
| lists[].standard_limit_i_lower | float\|null  | Ⅰ类下限值
| lists[].standard_limit_i_upper | float\|null  | Ⅰ类上限值                 |
| lists[].standard_limit_ii_lower | float\|null  | Ⅱ类下限值
| lists[].standard_limit_ii_upper | float\|null  | Ⅱ类上限值                 |
| lists[].standard_limit_iii_lower | float\|null  | Ⅲ类下限值
| lists[].standard_limit_iii_upper | float\|null  | Ⅲ类上限值                 |
| lists[].standard_limit_iv_lower | float\|null  | Ⅳ类下限值
| lists[].standard_limit_iv_upper | float\|null  | Ⅳ类上限值                 |
| lists[].standard_limit_v_lower | float\|null  | Ⅴ类下限值
| lists[].standard_limit_v_upper | float\|null  | Ⅴ类上限值                 |
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
    "standard_limit_i_lower": null,
  "standard_limit_i_upper": 0.02,
    "standard_limit_ii_lower": null,
  "standard_limit_ii_upper": 0.1,
    "standard_limit_iii_lower": null,
  "standard_limit_iii_upper": 0.2,
    "standard_limit_iv_lower": null,
  "standard_limit_iv_upper": 0.3,
    "standard_limit_v_lower": null,
  "standard_limit_v_upper": 0.4,
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
| standard_limit_i_lower | float\|null  | Ⅰ类下限值
| standard_limit_i_upper | float\|null  | Ⅰ类上限值                 |
| standard_limit_ii_lower | float\|null  | Ⅱ类下限值
| standard_limit_ii_upper | float\|null  | Ⅱ类上限值                 |
| standard_limit_iii_lower | float\|null  | Ⅲ类下限值
| standard_limit_iii_upper | float\|null  | Ⅲ类上限值                 |
| standard_limit_iv_lower | float\|null  | Ⅳ类下限值
| standard_limit_iv_upper | float\|null  | Ⅳ类上限值                 |
| standard_limit_v_lower | float\|null  | Ⅴ类下限值
| standard_limit_v_upper | float\|null  | Ⅴ类上限值                 |
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
  "standard_limit_i_lower": null,
  "standard_limit_i_upper": 0.02,
  "standard_limit_ii_lower": null,
  "standard_limit_ii_upper": 0.1,
  "standard_limit_iii_lower": null,
  "standard_limit_iii_upper": 0.2,
  "standard_limit_iv_lower": null,
  "standard_limit_iv_upper": 0.3,
  "standard_limit_v_lower": null,
  "standard_limit_v_upper": 0.4,
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

### 8.2 获取水库各指标最新监测值

- **GET** `/api/monitoring/last`
- **描述**：一次请求获取指定水库所有指标的最新监测值。需 admin 或 user 角色。
- **Content-Type**：application/json

| 参数          | 类型   | 位置   | 必填 | 说明                                  |
| ------------- | ------ | ------ | ---- | ------------------------------------- |
| Authorization | string | header | 是   | Bearer Token，格式 `Bearer <token>` |
| reservoir_id  | int    | query  | 是   | 水库 ID                               |

**请求示例**：

```
GET /api/monitoring/last?reservoir_id=1
Authorization: Bearer <token>
```

**响应格式**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "reservoir_id": 1,
    "records": [
      {
        "indicator_id": 3,
        "indicator_name": "溶解氧",
        "value": 6.82,
        "quality_flag": 1,
        "record_time": "2026-06-01 10:30:00"
      },
      {
        "indicator_id": 5,
        "indicator_name": "pH 值",
        "value": 7.35,
        "quality_flag": 1,
        "record_time": "2026-06-01 10:30:00"
      }
    ]
  }
}
```

| 字段                   | 类型     | 说明                                          |
| ---------------------- | -------- | --------------------------------------------- |
| reservoir_id           | int      | 水库 ID                                       |
| records[].indicator_id | int      | 指标 ID                                       |
| records[].indicator_name | string  | 指标名称                                      |
| records[].value        | float    | 监测值                                        |
| records[].quality_flag | int      | 数据质量标志：0 可疑，1 正常，2 无效          |
| records[].record_time  | datetime | 监测时间，格式 `YYYY-MM-DD HH:MM:SS`       |

**错误场景**：

| 错误码 | 场景                       |
| ------ | -------------------------- |
| 1002   | 数据不存在（该水库暂无监测数据） |

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

---

## 8.4 人工采样录入

- **POST** `/api/monitoring/manual-input`
- **描述**：监测员/管理员手动录入一条监测记录。需 admin 或 user 角色。
- **Content-Type**：application/json

| 参数          | 类型            | 位置   | 必填 | 说明                                  |
| ------------- | --------------- | ------ | ---- | ------------------------------------- |
| Authorization | string          | header | 是   | Bearer Token，格式 `Bearer <token>` |
| station_id    | int             | body   | 是   | 站点 ID                               |
| indicator_id  | int             | body   | 是   | 指标 ID                               |
| value         | float           | body   | 是   | 监测值                                |
| record_time   | datetime        | body   | 是   | 监测时间，格式 `YYYY-MM-DD HH:MM:SS` |
| quality_flag  | int\|null      | body   | 否   | 数据质量：0=可疑，1=正常，2=无效，默认1 |

**请求体示例**：

```json
{
  "station_id": 1,
  "indicator_id": 3,
  "value": 6.82,
  "record_time": "2026-06-03 10:30:00",
  "quality_flag": 1
}
```

**响应格式**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 19,
    "reservoir_id": 1,
    "station_id": 1,
    "indicator_id": 3,
    "value": 6.82,
    "record_time": "2026-06-03 10:30:00"
  }
}
```

| 字段          | 类型     | 说明                                      |
| ------------- | -------- | ----------------------------------------- |
| id            | int      | 监测记录 ID                               |
| reservoir_id  | int      | 水库 ID（从站点关联）                     |
| station_id    | int      | 站点 ID                                   |
| indicator_id  | int      | 指标 ID                                   |
| value         | float    | 监测值                                    |
| record_time   | datetime | 监测时间，格式 `YYYY-MM-DD HH:MM:SS`  |

**错误场景**：

| 错误码 | 场景                                  |
| ------ | ------------------------------------- |
| 1002   | 数据不存在（站点或指标不存在）        |
| 7001   | 资源已存在（该站点+指标+时间已存在）  |
| 5001   | 服务器内部错误                        |

---

## 九、仪表盘概览（/api/v1/dashboard）

仪表盘总览统计接口。需要 Bearer Token 认证，且要求 admin 或 user 角色。

### 9.1 获取仪表盘总览

- **GET** `/api/v1/dashboard/overview`
- **描述**：获取仪表盘首页总览统计。需要 Bearer Token 认证，需 admin 或 user 角色。
- **Content-Type**：application/json

| 参数          | 类型   | 位置   | 必填 | 说明                                  |
| ------------- | ------ | ------ | ---- | ------------------------------------- |
| Authorization | string | header | 是   | Bearer Token，格式 `Bearer <token>` |

**请求示例**：

```
GET /api/v1/dashboard/overview
Authorization: Bearer <token>
```

**响应格式**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "reservoir_count": 12,
    "normal_count": 45,
    "abnormal_count": 3,
    "alert_count": 8,
    "offline_stations": 2
  }
}
```

| 字段             | 类型 | 说明                         |
| ---------------- | ---- | ---------------------------- |
| reservoir_count  | int  | 启用水库总数                 |
| normal_count     | int  | 在线监测站点数               |
| abnormal_count   | int  | 可疑监测记录数（质量标志=0） |
| alert_count      | int  | 告警记录总数（质量标志 0/2） |
| offline_stations | int  | 离线监测站点数               |

**错误场景**：

| 错误码 | 场景                   |
| ------ | ---------------------- |
| 2003   | 权限不足               |
| 5001   | 系统内部错误           |

### 9.2 获取水库卡片列表

- **GET** `/api/v1/dashboard/reservoir-cards`
- **描述**：获取仪表盘页面所有启用状态的水库卡片列表，每个卡片包含水库基本信息、站点统计、告警数以及各核心指标的最新监测值。需要 Bearer Token 认证，需 admin 或 user 角色。
- **Content-Type**：application/json

| 参数          | 类型   | 位置   | 必填 | 说明                                  |
| ------------- | ------ | ------ | ---- | ------------------------------------- |
| Authorization | string | header | 是   | Bearer Token，格式 `Bearer <token>` |

**请求示例**：

```
GET /api/v1/dashboard/reservoir-cards
Authorization: Bearer <token>
```

**响应格式**：

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": 1,
      "name": "三峡水库",
      "code": "SX-001",
      "location": "湖北省宜昌市",
      "water_grade": "Ⅱ类",
      "watershed": "长江流域",
      "station_count": 5,
      "online_station_count": 4,
      "alert_count": 2,
      "indicators": [
        {
          "name": "溶解氧",
          "code": "rjy",
          "value": "6.5",
          "unit": "mg/L"
        },
        {
          "name": "氨氮",
          "code": "ad",
          "value": "0.35",
          "unit": "mg/L"
        }
      ]
    }
  ]
}
```

| 字段                        | 类型           | 说明                               |
| --------------------------- | -------------- | ---------------------------------- |
| data[].id                   | int            | 水库 ID                            |
| data[].name                 | string         | 水库名称                           |
| data[].code                 | string         | 水库编号                           |
| data[].location             | string\|null   | 所在位置                           |
| data[].water_grade          | string\|null   | 水质等级（如 Ⅱ类、Ⅲ类）           |
| data[].watershed            | string\|null   | 所属流域                           |
| data[].station_count        | int            | 站点总数                           |
| data[].online_station_count | int            | 在线站点数                         |
| data[].alert_count          | int            | 告警记录总数（quality_flag != 1）  |
| data[].indicators           | array          | 核心指标最新监测值列表             |
| indicators[].name           | string         | 指标名称                           |
| indicators[].code           | string         | 指标编码                           |
| indicators[].value          | string\|null   | 最新监测值（保留 4 位小数）       |
| indicators[].unit           | string\|null   | 单位                               |
| indicators[].code           | string         | 指标编码                           |
| indicators[].value          | string\|null   | 最新监测值（保留 4 位小数）       |
| indicators[].unit           | string\|null   | 单位                               |

**错误场景**：

| 错误码 | 场景                   |
| ------ | ---------------------- |
| 2003   | 权限不足               |
| 5001   | 系统内部错误           |

### 9.3 获取最近告警记录

- **GET** `/api/v1/dashboard/last-alert`
- **描述**：获取最近5条告警记录，用于仪表盘最新告警时间线展示。需要 Bearer Token 认证，需 admin 或 user 角色。
- **Content-Type**：application/json

| 参数          | 类型   | 位置   | 必填 | 说明                                  |
| ------------- | ------ | ------ | ---- | ------------------------------------- |
| Authorization | string | header | 是   | Bearer Token，格式 `Bearer <token>` |

**请求示例**：

```
GET /api/v1/dashboard/last-alert
Authorization: Bearer <token>
```

**响应格式**：

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "alert_id": 1,
      "reservoir_id": 1,
      "title": "总磷超标预警",
      "alert_level": 3,
      "indicators": [
        {
          "name": "总磷",
          "value": 0.35,
          "limit": 0.2
        }
      ],
      "status": "pending",
      "detected_at": "2026-06-01 08:30:00"
    }
  ]
}
```

| 字段                | 类型     | 说明                                                  |
| ------------------- | -------- | ----------------------------------------------------- |
| data[].alert_id     | int      | 告警 ID                                               |
| data[].reservoir_id | int      | 水库 ID                                               |
| data[].title        | string   | 告警标题                                              |
| data[].alert_level  | int      | 告警等级：1=info / 2=warning / 3=critical                   |
| data[].indicators   | array    | 超标指标列表，每项含 name/value/limit                 |
| data[].status       | int      | 状态：0=待确认 / 1=已确认 / 2=处置中 / 3=已解决     |
| data[].detected_at  | datetime | 检出时间，格式 `YYYY-MM-DD HH:MM:SS`               |

**错误场景**：

| 错误码 | 场景                   |
| ------ | ---------------------- |
| 2003   | 权限不足               |
| 5001   | 系统内部错误           |

---

## 十、预警管理（/api/v1/alerts）

预警列表查询接口。需要 Bearer Token 认证，admin 与 user 角色均可访问。

### 10.1 获取预警列表

- **GET** `/api/v1/alerts`
- **描述**：分页获取预警列表，支持按水库、预警等级、状态、检出时间范围筛选，按检出时间倒序。需 admin 或 user 角色。
- **Content-Type**：application/json

| 参数          | 类型            | 位置   | 必填 | 说明                                              |
| ------------- | --------------- | ------ | ---- | ------------------------------------------------- |
| Authorization | string          | header | 是   | Bearer Token，格式 `Bearer <token>`            |
| page          | int             | query  | 否   | 页码，默认 1                                      |
| page_size     | int             | query  | 否   | 每页记录数，默认 20，最大 100                     |
| reservoir_id  | int\|null       | query  | 否   | 水库 ID 筛选                                      |
| alert_level   | int\|null       | query  | 否   | 预警等级：1=info / 2=warning / 3=critical               |
| status        | int\|null       | query  | 否   | 状态：0=待确认 / 1=已确认 / 2=处置中 / 3=已解决     |
| start_time    | datetime\|null  | query  | 否   | 检出开始时间，格式 `YYYY-MM-DD HH:MM:SS`      |
| end_time      | datetime\|null  | query  | 否   | 检出结束时间，格式 `YYYY-MM-DD HH:MM:SS`      |

**请求示例**：

```
GET /api/v1/alerts?page=1&page_size=20&alert_level=3&status=0
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
        "handler_name": "张三",
        "title": "总磷超标预警",
        "alert_level": 3,
        "indicators": [
          {
            "name": "总磷",
            "value": 0.35,
            "limit": 0.2
          }
        ],
        "status": 0,
        "detected_at": "2026-06-02 08:30:00",
        "resolved_at": null
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 5,
      "total_pages": 1
    }
  }
}
```

| 字段                   | 类型            | 说明                                              |
| ---------------------- | --------------- | ------------------------------------------------- |
| lists[].id             | int             | 预警 ID                                           |
| lists[].reservoir_id   | int             | 水库 ID                                           |
| lists[].handler_name   | string\|null    | 处理人姓名（LEFT JOIN user 表获取）               |
| lists[].title          | string          | 预警标题                                          |
| lists[].alert_level    | int             | 预警等级：1=info / 2=warning / 3=critical               |
| lists[].indicators     | array\|null     | 超标指标列表 `[{name, value, limit}]`           |
| lists[].status         | int             | 状态：0=待确认 / 1=已确认 / 2=处置中 / 3=已解决     |
| lists[].detected_at    | datetime        | 检出时间，格式 `YYYY-MM-DD HH:MM:SS`          |
| lists[].resolved_at    | datetime\|null  | 解决时间，格式 `YYYY-MM-DD HH:MM:SS`          |
| pagination.page        | int             | 当前页码                                          |
| pagination.page_size   | int             | 每页数量                                          |
| pagination.total       | int             | 总记录数                                          |
| pagination.total_pages | int             | 总页数                                            |

**错误场景**：

| 错误码 | 场景                   |
| ------ | ---------------------- |
| 2003   | 权限不足               |
| 5001   | 系统内部错误           |

### 10.2 获取预警详情

- **GET** `/api/v1/alerts/{id}`
- **描述**：根据预警 ID 获取单条预警的完整详情。需 admin 或 user 角色。
- **Content-Type**：application/json

| 参数          | 类型   | 位置   | 必填 | 说明                                  |
| ------------- | ------ | ------ | ---- | ------------------------------------- |
| Authorization | string | header | 是   | Bearer Token，格式 `Bearer <token>` |
| id            | int    | path   | 是   | 预警 ID                               |

**请求示例**：

```
GET /api/v1/alerts/1
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
    "handler_id": null,
    "title": "梅山水库总磷超标预警",
    "alert_level": 3,
    "indicators": [
      {
        "name": "总磷",
        "value": 0.35,
        "limit": 0.2
      }
    ],
    "source_desc": "三峡大坝上游自动监测站连续 3 次监测数据超标",
    "suggestion": "立即排查上游污染源，启动应急监测方案",
    "status": 0,
    "detected_at": "2026-06-02 08:30:00",
    "resolved_at": null,
    "created_at": "2026-06-02 08:30:00"
  }
}
```

| 字段          | 类型            | 说明                                              |
| ------------- | --------------- | ------------------------------------------------- |
| id            | int             | 预警 ID                                           |
| reservoir_id  | int             | 水库 ID                                           |
| handler_id    | int\|null       | 处理人 ID                                         |
| title         | string          | 预警标题                                          |
| alert_level   | int             | 预警等级：1=info / 2=warning / 3=critical               |
| indicators    | array\|null     | 超标指标列表 `[{name, value, limit}]`           |
| source_desc   | string\|null    | 溯源描述                                          |
| suggestion    | string\|null    | 处置建议                                          |
| status        | int             | 状态：0=待确认 / 1=已确认 / 2=处置中 / 3=已解决 |
| detected_at   | datetime        | 检出时间，格式 `YYYY-MM-DD HH:MM:SS`          |
| resolved_at   | datetime\|null  | 解决时间，格式 `YYYY-MM-DD HH:MM:SS`          |
| created_at    | datetime        | 创建时间，格式 `YYYY-MM-DD HH:MM:SS`          |

**错误场景**：

| 错误码 | 场景                         |
| ------ | ---------------------------- |
| 1002   | 数据不存在（预警记录不存在） |

### 10.3 更新预警状态

- **PUT** `/api/v1/alerts/{id}`
- **描述**：更新预警状态，可同时指定处理人。需 admin 或 user 角色。
- **Content-Type**：application/json

| 参数          | 类型      | 位置   | 必填 | 说明                                              |
| ------------- | --------- | ------ | ---- | ------------------------------------------------- |
| Authorization | string    | header | 是   | Bearer Token，格式 `Bearer <token>`             |
| id            | int       | path   | 是   | 预警 ID                                           |
| status        | int       | body   | 是   | 状态：0=待确认 / 1=已确认 / 2=处置中 / 3=已解决 |
| handler_id    | int\|null | body   | 否   | 处理人 ID                                         |

**请求体示例**：

```json
{
  "status": 1,
  "handler_id": 1
}
```

**响应格式**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "reservoir_id": 1,
    "handler_id": 1,
    "title": "梅山水库总磷超标预警",
    "alert_level": 3,
    "indicators": [
      {
        "name": "总磷",
        "value": 0.35,
        "limit": 0.2
      }
    ],
    "source_desc": "三峡大坝上游自动监测站连续 3 次监测数据超标",
    "suggestion": "立即排查上游污染源，启动应急监测方案",
    "status": 1,
    "detected_at": "2026-06-02 08:30:00",
    "resolved_at": null
  }
}
```

| 字段          | 类型            | 说明                                              |
| ------------- | --------------- | ------------------------------------------------- |
| id            | int             | 预警 ID                                           |
| reservoir_id  | int             | 水库 ID                                           |
| handler_id    | int\|null       | 处理人 ID                                         |
| title         | string          | 预警标题                                          |
| alert_level   | int             | 预警等级：1=info / 2=warning / 3=critical               |
| indicators    | array\|null     | 超标指标列表 `[{name, value, limit}]`           |
| source_desc   | string\|null    | 溯源描述                                          |
| suggestion    | string\|null    | 处置建议                                          |
| status        | int             | 状态：0=待确认 / 1=已确认 / 2=处置中 / 3=已解决 |
| detected_at   | datetime        | 检出时间，格式 `YYYY-MM-DD HH:MM:SS`          |
| resolved_at   | datetime\|null  | 解决时间，格式 `YYYY-MM-DD HH:MM:SS`          |

**错误场景**：

| 错误码 | 场景                         |
| ------ | ---------------------------- |
| 1002   | 数据不存在（预警记录不存在） |

### 10.4 添加处置备注

- **POST** `/api/v1/alerts/{id}/notes`
- **描述**：为指定预警添加处置备注。需 admin 或 user 角色。
- **Content-Type**：application/json

| 参数          | 类型   | 位置   | 必填 | 说明                                  |
| ------------- | ------ | ------ | ---- | ------------------------------------- |
| Authorization | string | header | 是   | Bearer Token，格式 `Bearer <token>` |
| id            | int    | path   | 是   | 预警 ID                               |
| content       | string | body   | 是   | 备注内容                              |

**请求体示例**：

```json
{
  "content": "已通知现场人员复核采样点"
}
```

**响应格式**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "user_id": 1,
    "content": "已通知现场人员复核采样点",
    "created_at": "2026-06-03 10:30:00"
  }
}
```

| 字段       | 类型            | 说明     |
| ---------- | --------------- | -------- |
| id         | int             | 备注 ID  |
| user_id    | int\|null       | 创建人 ID |
| content    | string          | 备注内容 |
| created_at | datetime        | 创建时间 |

**错误场景**：

| 错误码 | 场景                     |
| ------ | ------------------------ |
| 1002   | 数据不存在（预警记录不存在） |

### 10.5 获取未读预警数

- **GET** `/api/v1/alerts/unread-count`
- **描述**：获取当前状态为待确认（status=0）的预警总数。需 admin 或 user 角色。
- **Content-Type**：application/json

| 参数          | 类型   | 位置   | 必填 | 说明                                  |
| ------------- | ------ | ------ | ---- | ------------------------------------- |
| Authorization | string | header | 是   | Bearer Token，格式 `Bearer <token>` |

**请求示例**：

```
GET /api/v1/alerts/unread-count
Authorization: Bearer <token>
```

**响应格式**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "count": 3
  }
}
```

| 字段  | 类型 | 说明                 |
| ----- | ---- | -------------------- |
| count | int  | 未读预警数（status=0） |

**错误场景**：

| 错误码 | 场景                   |
| ------ | ---------------------- |
| 5001   | 服务器内部错误         |

### 10.6 批量标记已读

- **PUT** `/api/v1/alerts/batch-read`
- **描述**：批量将指定预警的状态更新为已确认（status=1）。需 admin 或 user 角色。
- **Content-Type**：application/json

| 参数          | 类型        | 位置   | 必填 | 说明                                  |
| ------------- | ----------- | ------ | ---- | ------------------------------------- |
| Authorization | string      | header | 是   | Bearer Token，格式 `Bearer <token>` |
| ids           | array[int]  | body   | 是   | 预警 ID 列表                          |
| handler_id    | int\|null   | body   | 否   | 处理人 ID                             |

**请求体示例**：

```json
{
  "ids": [1, 2, 3],
  "handler_id": 1
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

| 错误码 | 场景                   |
| ------ | ---------------------- |
| 5001   | 服务器内部错误         |

---

## 十一、预警规则管理（/api/v1/alert-rules）

预警规则 CRUD 接口。需要 Bearer Token 认证，且要求 admin 角色。

### 11.1 获取预警规则列表

- **POST** `/api/v1/alert-rules/list`
- **描述**：分页获取预警规则列表，支持按指标、水库、启用状态筛选。需 admin 角色。
- **Content-Type**：application/json

| 参数          | 类型         | 位置   | 必填 | 说明                                  |
| ------------- | ------------ | ------ | ---- | ------------------------------------- |
| Authorization | string       | header | 是   | Bearer Token，格式 `Bearer <token>` |
| indicator_id  | int\|null    | body   | 否   | 指标 ID 筛选                          |
| reservoir_id  | int\|null    | body   | 否   | 水库 ID 筛选（null=全局规则）         |
| is_active     | int\|null    | body   | 否   | 启用状态筛选：0=禁用，1=启用          |
| page          | int          | body   | 是   | 页码，默认 1                          |
| page_size     | int          | body   | 是   | 每页记录数，默认 10                   |

**请求体示例**：

```json
{
  "indicator_id": null,
  "reservoir_id": null,
  "is_active": null,
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
        "rule_name": "COD超Ⅲ类限值-警告",
        "indicator_id": 3,
        "reservoir_id": null,
        "compare_direction": "gt",
        "trigger_class": "III",
        "alert_level": 2,
        "is_active": 1
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 10,
      "total": 10,
      "total_pages": 1
    }
  }
}
```

| 字段                   | 类型         | 说明                                              |
| ---------------------- | ------------ | ------------------------------------------------- |
| lists[].id             | int          | 规则 ID                                           |
| lists[].rule_name      | string       | 规则名称                                          |
| lists[].indicator_id   | int          | 关联指标 ID                                       |
| lists[].reservoir_id   | int\|null    | 水库 ID，null=全局规则                            |
| lists[].compare_direction | string     | 比较方向：gt=超上限告警，lt=低下限告警            |
| lists[].trigger_class  | string       | 触发限值等级：I/II/III/IV/V                       |
| lists[].alert_level    | int          | 预警等级：1=info / 2=warning / 3=critical         |
| lists[].is_active      | int          | 是否启用：0=禁用，1=启用                          |
| pagination.page        | int          | 当前页码                                          |
| pagination.page_size   | int          | 每页数量                                          |
| pagination.total       | int          | 总记录数                                          |
| pagination.total_pages | int          | 总页数                                            |

**错误场景**：

| 错误码 | 场景                   |
| ------ | ---------------------- |
| 2003   | 权限不足               |
| 5001   | 服务器内部错误         |

### 11.2 获取预警规则详情

- **GET** `/api/v1/alert-rules/{id}`
- **描述**：根据规则 ID 获取预警规则详细信息。需 admin 角色。
- **Content-Type**：application/json

| 参数          | 类型   | 位置   | 必填 | 说明                                  |
| ------------- | ------ | ------ | ---- | ------------------------------------- |
| Authorization | string | header | 是   | Bearer Token，格式 `Bearer <token>` |
| id            | int    | path   | 是   | 规则 ID                               |

**请求示例**：

```
GET /api/v1/alert-rules/1
Authorization: Bearer <token>
```

**响应格式**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "rule_name": "COD超Ⅲ类限值-警告",
    "indicator_id": 3,
    "reservoir_id": null,
    "compare_direction": "gt",
    "trigger_class": "III",
    "alert_level": 2,
    "is_active": 1,
    "remark": "化学需氧量超过20mg/L触发警告",
    "created_at": "2025-01-01T00:00:00",
    "updated_at": "2025-01-01T00:00:00"
  }
}
```

| 字段               | 类型         | 说明                                              |
| ------------------ | ------------ | ------------------------------------------------- |
| id                 | int          | 规则 ID                                           |
| rule_name          | string       | 规则名称                                          |
| indicator_id       | int          | 关联指标 ID                                       |
| reservoir_id       | int\|null    | 水库 ID，null=全局规则                            |
| compare_direction  | string       | 比较方向：gt=超上限告警，lt=低下限告警            |
| trigger_class      | string       | 触发限值等级：I/II/III/IV/V                       |
| alert_level        | int          | 预警等级：1=info / 2=warning / 3=critical         |
| is_active          | int          | 是否启用：0=禁用，1=启用                          |
| remark             | string\|null | 备注说明                                          |
| created_at         | datetime     | 创建时间                                          |
| updated_at         | datetime     | 更新时间                                          |

**错误场景**：

| 错误码 | 场景                     |
| ------ | ------------------------ |
| 1002   | 数据不存在（规则不存在） |
| 2003   | 权限不足                 |

### 11.3 创建预警规则

- **POST** `/api/v1/alert-rules/create`
- **描述**：管理员新增预警规则。需 admin 角色。
- **Content-Type**：application/json

| 参数              | 类型         | 位置   | 必填 | 说明                                              |
| ----------------- | ------------ | ------ | ---- | ------------------------------------------------- |
| Authorization     | string       | header | 是   | Bearer Token，格式 `Bearer <token>`           |
| rule_name         | string       | body   | 是   | 规则名称                                          |
| indicator_id      | int          | body   | 是   | 关联指标 ID                                       |
| reservoir_id      | int\|null    | body   | 否   | 水库 ID，不传或 null 表示全局规则                 |
| compare_direction | string       | body   | 是   | 比较方向：gt=超上限告警，lt=低下限告警            |
| trigger_class     | string       | body   | 是   | 触发限值等级：I/II/III/IV/V                       |
| alert_level       | int          | body   | 是   | 预警等级：1=info / 2=warning / 3=critical         |
| is_active         | int          | body   | 否   | 是否启用：0=禁用，1=启用，默认 1                  |
| remark            | string\|null | body   | 否   | 备注说明                                          |

**请求体示例**：

```json
{
  "rule_name": "COD超Ⅲ类限值-警告",
  "indicator_id": 3,
  "reservoir_id": null,
  "compare_direction": "gt",
  "trigger_class": "III",
  "alert_level": 2,
  "is_active": 1,
  "remark": "化学需氧量超过20mg/L触发警告"
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
| 1002   | 数据不存在（关联指标不存在） |
| 2003   | 权限不足                     |

### 11.4 更新预警规则

- **PUT** `/api/v1/alert-rules/{id}`
- **描述**：管理员更新预警规则信息。需 admin 角色。
- **Content-Type**：application/json

| 参数              | 类型         | 位置   | 必填 | 说明                                              |
| ----------------- | ------------ | ------ | ---- | ------------------------------------------------- |
| Authorization     | string       | header | 是   | Bearer Token，格式 `Bearer <token>`           |
| id                | int          | path   | 是   | 规则 ID                                           |
| rule_name         | string\|null | body   | 否   | 规则名称                                          |
| indicator_id      | int\|null    | body   | 否   | 关联指标 ID                                       |
| reservoir_id      | int\|null    | body   | 否   | 水库 ID，null=全局规则                            |
| compare_direction | string\|null | body   | 否   | 比较方向：gt=超上限告警，lt=低下限告警            |
| trigger_class     | string\|null | body   | 否   | 触发限值等级：I/II/III/IV/V                       |
| alert_level       | int\|null    | body   | 否   | 预警等级：1=info / 2=warning / 3=critical         |
| is_active         | int\|null    | body   | 否   | 是否启用：0=禁用，1=启用                          |
| remark            | string\|null | body   | 否   | 备注说明                                          |

**请求体示例**：

```json
{
  "rule_name": "COD超Ⅴ类限值-严重",
  "trigger_class": "V",
  "alert_level": 3
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
| 1002   | 数据不存在（规则不存在） |
| 2003   | 权限不足                 |

### 11.5 删除预警规则

- **DELETE** `/api/v1/alert-rules/{id}`
- **描述**：管理员删除指定预警规则。需 admin 角色。
- **Content-Type**：application/json

| 参数          | 类型   | 位置   | 必填 | 说明                                  |
| ------------- | ------ | ------ | ---- | ------------------------------------- |
| Authorization | string | header | 是   | Bearer Token，格式 `Bearer <token>` |
| id            | int    | path   | 是   | 规则 ID                               |

**请求示例**：

```
DELETE /api/v1/alert-rules/1
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
| 1002   | 数据不存在（规则不存在） |
| 2003   | 权限不足                 |

---

## 十二、WebSocket 实时预警推送（/ws/alerts）

### 12.1 连接地址

- **WS** `ws://localhost:3443/ws/alerts`
- **描述**：建立 WebSocket 连接后，后端在检测到新预警时主动推送 JSON 消息。无需认证，客户端保持连接存活即可。

### 消息格式

当预警规则判定触发、创建新预警后，服务端推送以下 JSON：

```json
{
  "type": "new_alert",
  "data": {
    "id": 6,
    "reservoir_id": 4,
    "title": "董铺水库指标告警（氨氮=1.80, 限值=1.0mg/L）",
    "alert_level": 2,
    "indicators": [
      {
        "name": "氨氮",
        "value": 1.8,
        "limit": 1.0,
        "unit": "mg/L"
      }
    ],
    "status": 0,
    "detected_at": "2026-06-03T10:30:00"
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 固定为 `new_alert` |
| data.id | int | 预警 ID |
| data.reservoir_id | int | 水库 ID |
| data.title | string | 预警标题 |
| data.alert_level | int | 1=info / 2=warning / 3=critical |
| data.indicators | array | 超标指标列表 |
| data.status | int | 状态：0=待确认 |
| data.detected_at | datetime | 检出时间，格式 ISO 8601 |

### 断线重连

- 服务端主动断开：前端 5 秒后自动重连
- 客户端页面关闭：连接自动断开

---

## 十三、知识库文档管理（/api/v1/documents）

知识库文档上传接口。需要 Bearer Token 认证，且要求 admin 角色。

### 13.1 上传文档

- **POST** `/api/v1/documents/upload`
- **描述**：批量上传知识库文档（PDF），自动进行文本解析、切片、向量化并存入 Chroma。需 admin 角色。
- **Content-Type**：multipart/form-data

| 参数          | 类型         | 位置   | 必填 | 说明                                  |
| ------------- | ------------ | ------ | ---- | ------------------------------------- |
| Authorization | string       | header | 是   | Bearer Token，格式 `Bearer <token>` |
| files         | list[file]   | body   | 是   | PDF 文件列表，单次最多 10 个，每个最大 50MB |
| category      | int          | body   | 是   | 文档类型：0=标准 1=案例 2=预案 3=其他 |

**请求示例**：

```
POST /api/v1/documents/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

files: 水质标准.pdf
files: 处置预案.pdf
category: 0
```

**响应格式**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 2,
    "success_count": 2,
    "failed_count": 0,
    "lists": [
      {
        "document_id": 1,
        "file_name": "水质标准.pdf",
        "file_size": 2048576,
        "status": 1,
        "error": null
      },
      {
        "document_id": 2,
        "file_name": "处置预案.pdf",
        "file_size": 1048576,
        "status": 1,
        "error": null
      }
    ]
  }
}
```

| 字段                   | 类型         | 说明                                   |
| ---------------------- | ------------ | -------------------------------------- |
| total                  | int          | 总文件数                               |
| success_count          | int          | 成功数                                 |
| failed_count           | int          | 失败数                                 |
| lists[].document_id    | int          | 文档 ID（校验失败为 0）               |
| lists[].file_name      | string       | 原始文件名                             |
| lists[].file_size      | int          | 文件大小（字节）                       |
| lists[].status         | int          | 处理状态：0=校验失败 1=处理中          |
| lists[].error          | string\|null | 校验失败原因                           |

**错误场景**：

| 错误码 | 场景                         |
| ------ | ---------------------------- |
| 3001   | 文件格式不支持               |
| 3002   | 文件大小超过限制             |
| 1001   | 参数错误（单次文件数超限）     |
| 2003   | 权限不足                     |
| 5001   | 服务器内部错误               |

---

## 十四、智能问答（/api/v1/chat）

SSE 流式对话接口。需要 Bearer Token 认证，admin 与 user 角色均可访问。

### 14.1 流式对话

- **POST** `/api/v1/chat`
- **描述**：发送用户问题，服务端以 SSE（Server-Sent Events）流式返回回答。

| 参数       | 类型       | 位置 | 必填 | 说明                    |
| ---------- | ---------- | ---- | ---- | ----------------------- |
| query      | string     | body | 是   | 用户问题（1-2000 字）   |
| session_id | int\|null  | body | 否   | 对话 ID，空则新建会话   |

**请求体示例**：

```json
{
  "query": "Ⅰ类水的溶解氧标准是多少？",
  "session_id": null
}
```

**响应（SSE 事件流）**：

Content-Type: `text/event-stream`

| 事件类型 | 字段               | 说明                       |
| -------- | ------------------ | -------------------------- |
| chunk    | content (string)   | 逐 token 流式回答内容      |
| done     | session_id, message_id | 回答完成，包含会话和消息 ID |

**事件示例**：

```
data: {"type":"chunk","content":"Ⅰ类"}

data: {"type":"chunk","content":"水的溶解氧标准为"}

data: {"type":"done","session_id":1,"message_id":2}
```

### 14.2 获取对话列表

- **GET** `/api/v1/chat`
- **描述**：分页获取当前用户的对话会话列表。

| 参数      | 类型 | 位置  | 必填 | 说明                    |
| --------- | ---- | ----- | ---- | ----------------------- |
| page      | int  | query | 否   | 页码，默认 1            |
| page_size | int  | query | 否   | 每页数量，默认 20       |

**响应格式**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "lists": [
      {
        "id": 1,
        "title": "Ⅰ类水的溶解氧标准是多少？",
        "created_at": "2026-06-05T10:30:00",
        "updated_at": "2026-06-05T10:35:00"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 1,
      "total_pages": 1
    }
  }
}
```

### 14.3 获取对话详情

- **GET** `/api/v1/chat/{id}`
- **描述**：获取指定对话的完整信息，包含消息列表。

| 参数 | 类型 | 位置 | 必填 | 说明   |
|------|------|------|------|--------|
| id   | int  | path | 是   | 对话ID |

**响应格式**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "title": "Ⅰ类水的溶解氧标准是多少？",
    "created_at": "2026-06-05T10:30:00",
    "updated_at": "2026-06-05T10:35:00",
    "messages": [
      {
        "id": 1,
        "session_id": 1,
        "role": "user",
        "content": "Ⅰ类水的溶解氧标准是多少？",
        "reference": null,
        "status": 0,
        "created_at": "2026-06-05T10:30:00"
      },
      {
        "id": 2,
        "session_id": 1,
        "role": "assistant",
        "content": "Ⅰ类水的溶解氧标准为...",
        "reference": [{"doc_id": 1, "chunk_index": 3}],
        "status": 0,
        "created_at": "2026-06-05T10:30:05"
      }
    ]
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 对话ID |
| title | string\|null | 对话标题 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |
| messages[].id | int | 消息ID |
| messages[].session_id | int | 对话ID |
| messages[].role | string | user / assistant |
| messages[].content | string | 消息内容 |
| messages[].reference | array\|null | 参考来源 [{doc_id, chunk_index}] |
| messages[].status | int | 0=活跃 1=废弃 |
| messages[].created_at | datetime | 创建时间 |

**错误场景**：

| 错误码 | 场景 |
|--------|------|
| 1002 | 会话不存在 |
| 2003 | 权限不足 |

### 13.5 重新处理文档

- **POST** `/api/v1/documents/{id}/reprocess`
- **描述**：重新处理指定知识库文档，清除旧内容后重新执行解析、切片和向量化。需 admin 角色。
- **Content-Type**：application/json

| 参数          | 类型   | 位置   | 必填 | 说明                                  |
| ------------- | ------ | ------ | ---- | ------------------------------------- |
| Authorization | string | header | 是   | Bearer Token，格式 `Bearer <token>` |
| id            | int    | path   | 是   | 文档 ID                               |

**请求示例**：

```
POST /api/v1/documents/1/reprocess
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
| 1002   | 数据不存在（文档不存在）     |
| 2003   | 权限不足                     |
| 5001   | 服务器内部错误               |

### 13.4 删除文档

- **DELETE** `/api/v1/documents/{id}`
- **描述**：删除知识库文档，同时清理物理文件和 Chroma 向量。需 admin 角色。
- **Content-Type**：application/json

| 参数          | 类型   | 位置   | 必填 | 说明                                  |
| ------------- | ------ | ------ | ---- | ------------------------------------- |
| Authorization | string | header | 是   | Bearer Token，格式 `Bearer <token>` |
| id            | int    | path   | 是   | 文档 ID                               |

**请求示例**：

```
DELETE /api/v1/documents/1
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
| 1002   | 数据不存在（文档不存在）     |
| 2003   | 权限不足                     |
| 5001   | 服务器内部错误               |

### 13.3 获取文档详情

- **GET** `/api/v1/documents/{id}`
- **描述**：根据文档 ID 获取知识库文档的完整详情（含元数据和解析文本）。需 admin 角色。
- **Content-Type**：application/json

| 参数          | 类型   | 位置   | 必填 | 说明                                  |
| ------------- | ------ | ------ | ---- | ------------------------------------- |
| Authorization | string | header | 是   | Bearer Token，格式 `Bearer <token>` |
| id            | int    | path   | 是   | 文档 ID                               |

**请求示例**：

```
GET /api/v1/documents/1
Authorization: Bearer <token>
```

**响应格式**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "title": "水质标准",
    "file_name": "水质标准.pdf",
    "file_size": 2048576,
    "doc_type": 0,
    "status": 2,
    "chunk_count": 24,
    "content": "文档解析后的纯文本内容...",
    "created_at": "2026-06-04T10:30:00",
    "updated_at": "2026-06-04T10:35:00"
  }
}
```

| 字段          | 类型         | 说明                                   |
| ------------- | ------------ | -------------------------------------- |
| id            | int          | 文档 ID                               |
| title         | string\|null | 文档标题                               |
| file_name     | string       | 原始文件名                             |
| file_size     | int          | 文件大小（字节）                       |
| doc_type      | int          | 文档类型：0=标准 1=案例 2=预案 3=其他 |
| status        | int          | 处理状态：0=已入库 1=解析中 2=已完成 3=失败 |
| chunk_count   | int          | 切片数量                               |
| content       | string\|null | 解析后的文本内容                       |
| created_at    | datetime     | 上传时间                               |
| updated_at    | datetime     | 更新时间                               |

**错误场景**：

| 错误码 | 场景                         |
| ------ | ---------------------------- |
| 1002   | 数据不存在（文档不存在）     |
| 2003   | 权限不足                     |
| 5001   | 服务器内部错误               |

### 13.2 获取文档列表

- **GET** `/api/v1/documents`
- **描述**：分页获取知识库文档列表，支持按文件名、文档类型、处理状态筛选。需 admin 角色。
- **Content-Type**：application/json

| 参数          | 类型         | 位置   | 必填 | 说明                                  |
| ------------- | ------------ | ------ | ---- | ------------------------------------- |
| Authorization | string       | header | 是   | Bearer Token，格式 `Bearer <token>` |
| keyword       | string\|null | query  | 否   | 文件名关键字（模糊搜索）              |
| doc_type      | int\|null    | query  | 否   | 文档类型：0=标准 1=案例 2=预案 3=其他 |
| status        | int\|null    | query  | 否   | 处理状态：0=已入库 1=解析中 2=已完成 3=失败 |
| page          | int          | query  | 否   | 页码，默认 1                          |
| page_size     | int          | query  | 否   | 每页数量，默认 15                     |

**请求示例**：

```
GET /api/v1/documents?keyword=水质&doc_type=0&status=2&page=1&page_size=15
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
        "title": "水质标准",
        "file_name": "水质标准.pdf",
        "file_size": 2048576,
        "doc_type": 0,
        "status": 2,
        "chunk_count": 24,
        "created_at": "2026-06-04T10:30:00"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 15,
      "total": 1,
      "total_pages": 1
    }
  }
}
```

| 字段                   | 类型         | 说明                                   |
| ---------------------- | ------------ | -------------------------------------- |
| lists[].id             | int          | 文档 ID                               |
| lists[].title          | string\|null | 文档标题                               |
| lists[].file_name      | string       | 原始文件名                             |
| lists[].file_size      | int          | 文件大小（字节）                       |
| lists[].doc_type       | int          | 文档类型：0=标准 1=案例 2=预案 3=其他 |
| lists[].status         | int          | 处理状态：0=已入库 1=解析中 2=已完成 3=失败 |
| lists[].chunk_count    | int          | 切片数量                               |
| lists[].created_at     | datetime     | 上传时间                               |
| pagination.page        | int          | 当前页码                               |
| pagination.page_size   | int          | 每页数量                               |
| pagination.total       | int          | 总记录数                               |
| pagination.total_pages | int          | 总页数                                 |

**错误场景**：

| 错误码 | 场景                         |
| ------ | ---------------------------- |
| 2003   | 权限不足                     |
| 5001   | 服务器内部错误               |
