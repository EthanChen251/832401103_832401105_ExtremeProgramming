"""管理本地 SQLite 连接以及通讯录的查询和写入。"""

import sqlite3
from typing import Any

from flask import current_app, g

CONTACT_FIELDS = ("name", "notes", "favorite")
CONTACT_QUERY = """
    SELECT c.id, c.name, c.notes, c.favorite, c.created_at, c.updated_at,
           m.type AS method_type, m.value AS method_value
    FROM contacts AS c
    LEFT JOIN contact_methods AS m ON m.contact_id = c.id
"""
CONTACT_ORDER = """
    ORDER BY c.id, CASE m.type
        WHEN 'phone' THEN 0
        WHEN 'email' THEN 1
        WHEN 'social' THEN 2
        WHEN 'address' THEN 3
    END, m.position
"""


def get_db() -> sqlite3.Connection:
    """按需打开当前 Flask 应用上下文的数据库连接并启用外键。"""
    connection = g.get("db")
    if connection is None:
        connection = sqlite3.connect(current_app.config["DATABASE"])
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        g.db = connection
    return connection


def close_db(_error: BaseException | None = None) -> None:
    """在应用上下文结束时关闭已打开的数据库连接。"""
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def init_db() -> None:
    """执行建表脚本，创建缺失的表和索引。"""
    with current_app.open_resource(
        "schema.sql", "r", encoding="utf-8"
    ) as schema:
        get_db().executescript(schema.read())


def select_contacts(
    *, contact_id: int | None = None, favorite: bool | None = None
) -> list[dict[str, Any]]:
    """在一次查询中读取联系人和联系方式，可按 ID 或收藏状态筛选。"""
    filters = []
    params = []
    if contact_id is not None:
        filters.append("c.id = ?")
        params.append(contact_id)
    if favorite is not None:
        filters.append("c.favorite = ?")
        params.append(int(favorite))

    query = CONTACT_QUERY
    if filters:
        query += " WHERE " + " AND ".join(filters)
    cursor = get_db().execute(query + CONTACT_ORDER, params)
    contacts: dict[int, dict[str, Any]] = {}
    for row in cursor:
        contact = contacts.get(row["id"])
        if contact is None:
            contact = {
                "id": row["id"],
                "name": row["name"],
                "notes": row["notes"],
                "favorite": bool(row["favorite"]),
                "methods": [],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            contacts[row["id"]] = contact
        if row["method_type"] is not None:
            contact["methods"].append(
                {"type": row["method_type"], "value": row["method_value"]}
            )
    return list(contacts.values())


def create_contact(data: dict[str, Any]) -> dict[str, Any]:
    """在一个事务内新增联系人及其联系方式，返回完整联系人。"""
    connection = get_db()
    with connection:
        contact_id = _insert_contact(connection, data)
        return select_contacts(contact_id=contact_id)[0]


def update_contact(
    contact_id: int, data: dict[str, Any]
) -> dict[str, Any] | None:
    """原子更新给定字段，必要时替换联系方式，找不到联系人时返回空值。"""
    fields = [field for field in CONTACT_FIELDS if field in data]
    changes = [f"{field} = ?" for field in fields]
    # 连续请求落在同一毫秒时，更新时间也应发生变化。
    changes.append(
        "updated_at = max("
        "strftime('%Y-%m-%dT%H:%M:%fZ', 'now'), "
        "strftime('%Y-%m-%dT%H:%M:%fZ', updated_at, '+0.001 seconds'))"
    )
    params = [data[field] for field in fields]
    params.append(contact_id)

    connection = get_db()
    with connection:
        cursor = connection.execute(
            f"UPDATE contacts SET {', '.join(changes)} WHERE id = ?", params
        )
        if cursor.rowcount == 0:
            return None
        if "methods" in data:
            _replace_methods(connection, contact_id, data["methods"])
        return select_contacts(contact_id=contact_id)[0]


def delete_contact(contact_id: int) -> bool:
    """删除指定联系人并级联删除联系方式，返回是否删到记录。"""
    connection = get_db()
    with connection:
        cursor = connection.execute(
            "DELETE FROM contacts WHERE id = ?", (contact_id,)
        )
        return cursor.rowcount == 1


def insert_contacts(contacts: list[dict[str, Any]]) -> int:
    """在同一个事务内导入所有已校验联系人，返回写入数量。"""
    connection = get_db()
    with connection:
        for contact in contacts:
            _insert_contact(connection, contact)
    return len(contacts)


def _insert_contact(
    connection: sqlite3.Connection, data: dict[str, Any]
) -> int:
    """在调用方的事务内插入联系人和联系方式并返回新 ID。"""
    cursor = connection.execute(
        "INSERT INTO contacts (name, notes, favorite) VALUES (?, ?, ?)",
        (data["name"], data["notes"], int(data["favorite"])),
    )
    contact_id = cursor.lastrowid
    if contact_id is None:
        raise RuntimeError("SQLite 未返回新联系人的 ID。")
    if data["methods"]:
        _replace_methods(connection, contact_id, data["methods"])
    return contact_id


def _replace_methods(
    connection: sqlite3.Connection,
    contact_id: int,
    methods: list[dict[str, str]],
) -> None:
    """在调用方的事务内替换全部联系方式，按类别分配连续位置。"""
    connection.execute(
        "DELETE FROM contact_methods WHERE contact_id = ?", (contact_id,)
    )
    positions: dict[str, int] = {}
    rows = []
    for method in methods:
        method_type = method["type"]
        position = positions.get(method_type, 0)
        rows.append((contact_id, method_type, position, method["value"]))
        positions[method_type] = position + 1
    connection.executemany(
        "INSERT INTO contact_methods (contact_id, type, position, value) "
        "VALUES (?, ?, ?, ?)",
        rows,
    )
