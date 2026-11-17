# Contact Manager（通讯录管理系统）

本项目是 Software Engineering (FZU–MU) 的 Extreme Programming 作业。Vue 3 + Vite 提供网页界面，Python + Flask 提供 REST API，SQLite 在后端本地磁盘保存数据。当前设计覆盖单个通讯录：联系人增删改查、收藏、多种联系方式及 Excel 导入导出。

课程要求、开发计划与交付物见[中文版计划书](docs/XP_Contact_Manager_Project_Plan_CN.md)和[英文版计划书](docs/XP_Contact_Manager_Project_Plan_EN.md)。本文定义前后端开发共用的接口和数据格式；搜索、用户账号及云端部署不在本接口的范围内。

## 1. 联系人数据与校验

### 账号与数据范围（本次扩展）

客户端以 JSON 向 `POST /api/v1/auth/register` 或 `POST /api/v1/auth/login` 提交 `{"name":"用户名","password":"密码"}`。注册成功即登录，两者返回 `{"user":{"id":1,"name":"用户名"}}` 并设置 HttpOnly 会话 Cookie，有效期七天。重复注册返回 409，登录凭据错误返回 401。`GET /api/v1/auth/session` 恢复会话，未登录返回 `{"user":null}`。`POST /api/v1/auth/logout` 发送空 JSON 对象并撤销当前会话。

本次扩展将数据范围调整为每个账号一个通讯录。当前列表接口要求登录，未登录返回 401。账号信息存入 Flask instance 目录下的 `accounts.sqlite3`，每个账号按服务端生成的数字 ID 使用独立的 `contacts-<id>.sqlite3`。后续增删改、收藏和 Excel 接口均应从已验证的会话取得用户 ID，复用 `contact_database(user_id)`，每个文件沿用下文相同的联系人表结构。

一个联系人可以有零到多条联系方式。同一类型可以保存多个值。API、SQLite 和 Excel 使用同一套业务校验：Flask 在写入前校验，SQLite 约束作为第二道检查。

| JSON 字段 | 类型 | 写入规则 |
| --- | --- | --- |
| `name` | 字符串 | 新增必填；去除首尾空白后为 1–100 个字符，不含换行；允许重名。 |
| `notes` | 字符串 | 默认 `""`；最多 2,000 个字符；保留空格，换行统一成 LF。 |
| `favorite` | 布尔值 | 默认 `false`；JSON 只接受 `true` 或 `false`。 |
| `methods` | 对象数组 | 默认 `[]`；每项必须且只能包含 `type` 和 `value`。每种类型最多 20 条。同一联系人同一类型中，去除 `value` 首尾空白后完全相同的值不可重复，比较区分大小写。 |
| `methods[].type` | 字符串 | 只接受 `phone`、`email`、`social`、`address`，分别表示电话、邮箱、社交账号和地址。 |
| `methods[].value` | 字符串 | 去除首尾空白后为 1–500 个字符，不含换行；保持原有的大小写、前导零和符号。 |
| `id` | 正整数 | 服务端生成，范围为 1 至 9,007,199,254,740,991，只读。 |
| `created_at`、`updated_at` | 字符串 | 服务端生成的 UTC 时间，例如 `2026-11-16T08:30:00.000Z`，只读。 |

- 电话至少含一个 ASCII 数字，允许数字、空格和 `+()- .`，按字符串保存。邮箱用 `[^@\s]+@[^@\s]+\.[^@\s]+` 对整个值做基本格式检查。社交账号和地址使用通用文本规则。
- 字符长度按 Unicode 码点计。为保证可写入 Excel，在处理原始文本前先检查它是有效的 Unicode，且不含 U+0000–U+001F 中除制表符、LF、CR 以外的控制字符，也不含 U+FFFE 或 U+FFFF。检查姓名和联系方式是否有换行时，先去除首尾空白。
- 联系方式输出按 `phone` → `email` → `social` → `address` 分组；同类内部保留提交时的顺序。联系方式通过联系人对象一起编辑，没有独立的公开 ID。
- API 拒绝未知字段、只读字段和 `null`。新增时省略可选字段才使用默认值；编辑时省略字段表示保留原值。

## 2. REST API

前端发送相对路径 `/api/v1/...` 的请求，开发时由 Vite 将 `/api` 转发到 Flask。JSON 请求使用 `Content-Type: application/json`，JSON 响应使用 `application/json`。联系人详情直接返回对象，列表用 `items` 包装。上传和下载使用下表约定的文件格式。

| 方法与路径 | 输入与行为 | 成功响应 |
| --- | --- | --- |
| `GET /api/v1/contacts` | 列出全部联系人，按 `id` 升序。可传 `favorite=true` 只看收藏，或 `favorite=false` 只看未收藏。无匹配结果时返回 `{"items":[]}`。 | `200`，`{"items":[联系人对象, ...]}` |
| `POST /api/v1/contacts` | 提交 `name` 和任意可选字段 `notes`、`favorite`、`methods`。 | `201`，联系人对象；`Location: /api/v1/contacts/{id}` |
| `GET /api/v1/contacts/{id}` | 读取一位联系人的完整信息。 | `200`，联系人对象 |
| `PATCH /api/v1/contacts/{id}` | 提交至少一个可写字段。`methods` 有值时整体替换，传 `[]` 清空；`notes: ""` 清空备注。收藏和取消收藏只需修改 `favorite`。 | `200`，更新后的联系人对象 |
| `DELETE /api/v1/contacts/{id}` | 删除联系人及其全部联系方式。 | `204`，无响应体 |
| `POST /api/v1/contacts/import` | `multipart/form-data`，文件字段 `file` 必须且只能出现一次，上传一个 `.xlsx` 文件。 | `200`，如 `{"imported_count":2}` |
| `GET /api/v1/contacts/export` | 导出整个通讯录，包括未收藏的联系人；按 `id` 升序。通讯录为空时仅导出表头。 | `200`，`.xlsx` 文件，`Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`，`Content-Disposition: attachment; filename="contacts.xlsx"` |

`favorite` 查询参数只接受小写的 `true` 或 `false`，重复传入或取其他值时返回 `400`。`{id}` 必须是合法的正整数且对应一位现有联系人，否则返回 `404`。新增时两个时间字段取同一值；每次成功 `PATCH` 写入新的 `updated_at`，`created_at` 保持原值。

**新增示例**：`POST /api/v1/contacts`

```json
{
  "name": "林晓",
  "notes": "课程联系人",
  "methods": [
    {"type": "phone", "value": "0591-5550123"},
    {"type": "phone", "value": "+86 13800000000"},
    {"type": "email", "value": "lin.xiao@example.com"}
  ]
}
```

响应 `201 Created`，`Location: /api/v1/contacts/42`。`GET /api/v1/contacts/42` 返回同样的 JSON 结构，状态码为 `200`。

```json
{
  "id": 42,
  "name": "林晓",
  "notes": "课程联系人",
  "favorite": false,
  "methods": [
    {"type": "phone", "value": "0591-5550123"},
    {"type": "phone", "value": "+86 13800000000"},
    {"type": "email", "value": "lin.xiao@example.com"}
  ],
  "created_at": "2026-11-16T08:30:00.000Z",
  "updated_at": "2026-11-16T08:30:00.000Z"
}
```

**收藏与编辑示例**：`PATCH /api/v1/contacts/42` 传 `{"favorite":true}` 即可收藏，传 `{"favorite":false}` 取消收藏，其他信息保持原值。收藏页请求 `GET /api/v1/contacts?favorite=true`，其 `items` 数组包含匹配的完整联系人对象。若要把该联系人的全部联系方式换成一个邮箱，则提交 `{"methods":[{"type":"email","value":"lin.xiao@example.com"}]}`。

**导入示例**：若 Flask 在本机 `5000` 端口运行，执行以下命令上传当前目录的文件。成功时返回 `200` 和实际写入的联系人数量。

```shell
curl -F "file=@contacts.xlsx" http://127.0.0.1:5000/api/v1/contacts/import
```

**错误格式**：统一返回 `error.code`（供前端判断）、`error.message`（供展示）和 `error.details`（数组，没有细节时为 `[]`）。JSON 字段错误使用 `field`，如 `methods[0].value`；Excel 表头或数据错误可附 `row`（从 1 开始）和 `field`（列名）。前端按 HTTP 状态和 `code` 判断结果。

| HTTP 状态 | `error.code` | 触发条件 |
| --- | --- | --- |
| `400` | `BAD_REQUEST` | JSON 语法错误、收藏筛选参数无效、上传请求缺少 `file` 或提供了多个 `file`。 |
| `404` | `NOT_FOUND` | 联系人或 API 路径不存在。 |
| `405` | `METHOD_NOT_ALLOWED` | API 路径不支持该请求方法，保留 `Allow` 响应头。 |
| `415` | `UNSUPPORTED_MEDIA_TYPE` | JSON 或上传请求的 `Content-Type` 不符合接口约定，或上传文件扩展名不是 `.xlsx`（忽略大小写）。 |
| `422` | `VALIDATION_ERROR` | JSON 可解析但字段或结构无效，例如空姓名、重复联系方式或空的 `PATCH` 对象。 |
| `422` | `INVALID_WORKBOOK` | `.xlsx` 文件不可读取、缺少指定工作表、表头不匹配或有数据校验错误。 |
| `422` | `EXPORT_LIMIT_EXCEEDED` | 联系人数超出一个 `.xlsx` 工作表可容纳的数据行数。 |
| `500` | `INTERNAL_ERROR` | 意外的数据库或文件处理错误；响应不包含内部异常和文件路径。 |

例如，导入时第 3 行 `name` 为空，响应为 `422`：

```json
{
  "error": {
    "code": "INVALID_WORKBOOK",
    "message": "工作簿校验失败，未导入任何联系人。",
    "details": [{"row": 3, "field": "name", "message": "姓名不能为空。"}]
  }
}
```

## 3. SQLite 表结构

`contacts` 存放联系人，`contact_methods` 存放联系方式，两表通过 `contact_id` 建立一对多关系。`position` 是同一联系人、同一类型内从 0 开始的顺序；导出和查询时按类型及 `position` 排列。`favorite` 在数据库中存为 `0` 或 `1`，在 API 中转换为布尔值。

```sql
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS contacts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT
                CHECK (id BETWEEN 1 AND 9007199254740991),
    name        TEXT NOT NULL CHECK (
                    typeof(name) = 'text' AND length(name) BETWEEN 1 AND 100
                    AND instr(name, char(10)) = 0 AND instr(name, char(13)) = 0
                ),
    notes       TEXT NOT NULL DEFAULT '' CHECK (typeof(notes) = 'text' AND length(notes) <= 2000),
    favorite    INTEGER NOT NULL DEFAULT 0 CHECK (favorite IN (0, 1)),
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS contact_methods (
    contact_id  INTEGER NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    type        TEXT NOT NULL CHECK (type IN ('phone', 'email', 'social', 'address')),
    position    INTEGER NOT NULL CHECK (typeof(position) = 'integer' AND position BETWEEN 0 AND 19),
    value       TEXT NOT NULL CHECK (
                    typeof(value) = 'text' AND length(value) BETWEEN 1 AND 500
                    AND instr(value, char(10)) = 0 AND instr(value, char(13)) = 0
                ),
    PRIMARY KEY (contact_id, type, position),
    UNIQUE (contact_id, type, value)
);

CREATE INDEX IF NOT EXISTS idx_contacts_favorite_id ON contacts(favorite, id);
```

- Flask 始终打开同一个本地文件，例如 `instance/contacts.sqlite3`，启动时按需创建缺失的表和索引。每个连接都在事务开始前执行 `PRAGMA foreign_keys = ON`。
- Flask 负责去除首尾空白、检查文本格式并为每种类型分配连续的 `position`。创建、编辑、删除单个联系人时，各自用一个事务完成；若编辑包含 `methods`，在同一事务中删除旧方法、写入新方法并更新联系人。任何一步失败都回滚。
- `updated_at` 在执行 `PATCH` 时由后端显式更新；仅依靠 SQL 的默认值不会自动更新时间。

## 4. Excel 文件格式与导入规则

格式为 `.xlsx`。读取名为 `Contacts` 的工作表，其他工作表忽略。第 1 行必须是以下七个表头，顺序、大小写固定；第 2 行起每位联系人占一行。导出保留姓名、备注、收藏和所有联系方式；`id`、创建及更新时间由数据库管理，不写入 Excel。

| 列 | 表头 | 单元格说明 |
| --- | --- | --- |
| A | `name` | 必填文本，按姓名规则校验。 |
| B | `notes` | 可空文本，支持多行。 |
| C | `favorite` | Excel 布尔值，或文本 `TRUE` / `FALSE`（忽略大小写及首尾空白）；空白表示 `false`。 |
| D | `phones` | 电话。文本单元格，同类每行一条。 |
| E | `emails` | 邮箱。文本单元格，同类每行一条。 |
| F | `socials` | 社交账号。文本单元格，同类每行一条。 |
| G | `addresses` | 地址。文本单元格，同类每行一条。 |

| name | notes | favorite | phones | emails | socials | addresses |
| --- | --- | --- | --- | --- | --- | --- |
| 林晓 | 课程联系人 | FALSE | 0591-5550123<br>+86 13800000000 | lin.xiao@example.com | @linxiao | 福州市大学城某路 1 号 |

示例中的两个号码在同一个 `phones` 单元格内，用实际换行分隔；在 Windows Excel 中可用 **Alt+Enter** 插入换行。编辑前将联系方式列设为文本，保留电话号码的前导零和加号。多值列不按逗号或分号拆分，带逗号的地址仍是一条。

1. **检查文件和表头。** 确认文件可读、有 `Contacts` 工作表、A1:G1 与表头完全一致。拒绝表头或数据行在 G 列右侧出现有内容的单元格。
2. **检查单元格。** 忽略七列都为空单元格或空字符串的行。拒绝所读区域中的公式及错误值；文本列拒绝数字、日期等非文本值，提示用户把原值以文本重新录入。Excel 布尔值只用于 `favorite`。多值列将 CRLF、CR 统一为 LF，按 LF 分行，去除每项首尾空白并忽略空行，再按第 1 节校验。备注保留原文本，只统一换行并应用第 1 节的校验。
3. **校验后整批追加。** 校验所有数据行并返回可定位的行号及列名。存在任何错误则返回 `422`，不写入有效行；全部通过后在同一个 SQLite 事务中写入所有联系人和联系方式。文件仅有表头时返回 `{"imported_count":0}`。导入不按姓名或联系方式做跨联系人合并，每次导入都会为每一行分配新 ID，重复导入会追加同样的数据。
4. **导出同一种格式。** 从一次一致的数据库读取生成工作簿，收藏写为 Excel 布尔值，文本列明确写成文本，即使值以 `=` 或 `+` 开头也不生成公式。空备注和空联系方式可留空。导出的文件可直接导入；往返时保留业务字段及同类联系方式顺序，生成新的 ID 和时间。

## 5. 实现后的验收要点

- 新增含两个电话号码的联系人，修改备注和收藏后重启后端；详情、收藏列表和号码顺序应保持正确。
- `PATCH` 只传 `favorite` 时联系方式保持原值；传 `methods: []` 时清空联系方式；删除联系人后不能再查到该联系人，数据库中也没有其联系方式。
- 将含多种联系方式、收藏、前导零和多行备注的通讯录导出并导入空数据库，比较姓名、备注、收藏及联系方式。再使用含坏表头、公式、数字型电话或缺失姓名的文件验证错误定位和整批回滚。
