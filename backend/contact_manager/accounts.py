import hashlib
import secrets
import sqlite3
import time
from pathlib import Path

from flask import Blueprint, current_app, g, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

api = Blueprint("accounts", __name__, url_prefix="/api/v1")
COOKIE = "contact_session"
LIFETIME = 7 * 24 * 3600


def database(key, filename):
    if key not in g:
        folder = Path(current_app.instance_path)
        folder.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(folder / filename)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        setattr(g, key, connection)
    return getattr(g, key)


def accounts():
    db = database("accounts_db", "accounts.sqlite3")
    db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sessions (
            digest TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
            expires INTEGER NOT NULL
        );
    """)
    return db


@api.teardown_app_request
def close_connections(error):
    for key in ("accounts_db", "contacts_db"):
        db = g.pop(key, None)
        if db is not None:
            db.close()


def digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def current_user():
    return accounts().execute("""
        SELECT users.id, users.name FROM sessions JOIN users ON users.id = sessions.user_id
        WHERE digest = ? AND expires > ?
    """, (digest(request.cookies.get(COOKIE, "")), int(time.time()))).fetchone()


@api.after_request
def private_response(response):
    response.headers["Cache-Control"] = "no-store"
    return response


@api.get("/auth/session")
def session():
    user = current_user()
    return jsonify(user=dict(user) if user else None)


@api.post("/auth/login")
@api.post("/auth/register")
def authenticate():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(message="请提交用户名和密码。"), 400
    name, password = data.get("name"), data.get("password")
    if not isinstance(name, str) or not isinstance(password, str):
        return jsonify(message="请输入用户名和密码。"), 400
    name = name.strip()
    if not 1 <= len(name) <= 40 or not 8 <= len(password) <= 128:
        return jsonify(message="用户名限 1–40 字，密码限 8–128 个字符。"), 400
    db = accounts()
    with db:
        if request.path.endswith("/register"):
            try:
                user_id = db.execute("INSERT INTO users(name,password_hash) VALUES (?,?)",
                                     (name, generate_password_hash(password))).lastrowid
            except sqlite3.IntegrityError:
                return jsonify(message="这个用户名已被使用。"), 409
        else:
            user = db.execute("SELECT * FROM users WHERE name=?", (name,)).fetchone()
            if user is None or not check_password_hash(user["password_hash"], password):
                return jsonify(message="用户名或密码有误。"), 401
            user_id = user["id"]
        token = secrets.token_urlsafe(32)
        now = int(time.time())
        db.execute("DELETE FROM sessions WHERE expires <= ? OR digest = ?",
                   (now, digest(request.cookies.get(COOKIE, ""))))
        db.execute("INSERT INTO sessions VALUES (?,?,?)", (digest(token), user_id, now + LIFETIME))
    response = jsonify(user={"id": user_id, "name": name})
    response.set_cookie(COOKIE, token, max_age=LIFETIME, httponly=True,
                        secure=request.is_secure, samesite="Lax", path="/api/v1")
    return response


@api.post("/auth/logout")
def logout():
    if not request.is_json:
        return jsonify(message="请使用 JSON 请求。"), 415
    db = accounts()
    with db:
        db.execute("DELETE FROM sessions WHERE digest=?", (digest(request.cookies.get(COOKIE, "")),))
    response = jsonify(user=None)
    response.delete_cookie(COOKIE, path="/api/v1")
    return response


def contact_database(user_id):
    db = database("contacts_db", f"contacts-{user_id}.sqlite3")
    db.executescript(Path(__file__).with_name("contacts.sql").read_text(encoding="utf-8"))
    return db


@api.get("/contacts")
def list_contacts():
    user = current_user()
    if user is None:
        return jsonify(message="请先登录。"), 401
    db = contact_database(user["id"])
    filters = request.args.getlist("favorite")
    if filters and filters not in (["true"], ["false"]):
        return jsonify(message="收藏筛选参数无效。"), 400
    sql = "SELECT * FROM contacts"
    params = ()
    if filters:
        sql += " WHERE favorite=?"
        params = (filters == ["true"],)
    items = {}
    db.execute("BEGIN")
    for row in db.execute(sql + " ORDER BY id", params):
        items[row["id"]] = dict(row, favorite=bool(row["favorite"]), methods=[])
    for row in db.execute("""SELECT * FROM contact_methods ORDER BY contact_id,
                           CASE type WHEN 'phone' THEN 0 WHEN 'email' THEN 1
                           WHEN 'social' THEN 2 ELSE 3 END, position"""):
        if row["contact_id"] in items:
            items[row["contact_id"]]["methods"].append({"type": row["type"], "value": row["value"]})
    return jsonify(items=list(items.values()))
