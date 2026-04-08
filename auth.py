import hashlib
from typing import Optional

import streamlit as st
import pandas as pd
from sqlalchemy import text

from db import get_conn, get_engine, now_str


DEFAULT_USERS = [
    {"username": "admin", "password": "admin123", "name": "系統管理員", "role": "admin", "team": "企劃課－行政組"},
    {"username": "supervisor", "password": "supervisor123", "name": "支援主管", "role": "supervisor", "team": "企劃課－行政組"},
    {"username": "staff01", "password": "staff123", "name": "測試人員", "role": "staff", "team": "進貨課－進貨組"},
]


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def init_auth_table() -> None:
    engine = get_engine()
    is_postgres = engine.dialect.name == "postgresql"
    auto_id = "SERIAL PRIMARY KEY" if is_postgres else "INTEGER PRIMARY KEY AUTOINCREMENT"
    with get_conn() as conn:
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS users (
                id {auto_id},
                username VARCHAR(100) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                display_name VARCHAR(100) NOT NULL,
                role VARCHAR(20) NOT NULL,
                team VARCHAR(100),
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at VARCHAR(30) NOT NULL,
                updated_at VARCHAR(30) NOT NULL
            )
        """))
        for user in DEFAULT_USERS:
            conn.execute(text("""
                INSERT INTO users (username, password_hash, display_name, role, team, is_active, created_at, updated_at)
                SELECT :username, :password_hash, :display_name, :role, :team, 1, :created_at, :updated_at
                WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = :username)
            """), {
                "username": user["username"],
                "password_hash": hash_password(user["password"]),
                "display_name": user["name"],
                "role": user["role"],
                "team": user["team"],
                "created_at": now_str(),
                "updated_at": now_str(),
            })


def verify_user(username: str, password: str) -> Optional[dict]:
    init_auth_table()
    with get_conn() as conn:
        row = conn.execute(text("""
            SELECT id, username, display_name, role, team
            FROM users
            WHERE username = :username AND password_hash = :password_hash AND is_active = 1
        """), {
            "username": username.strip(),
            "password_hash": hash_password(password),
        }).mappings().first()
    return dict(row) if row else None


def login(username: str, password: str) -> bool:
    user = verify_user(username, password)
    if not user:
        return False
    st.session_state["logged_in"] = True
    st.session_state["user"] = user
    return True


def logout() -> None:
    st.session_state["logged_in"] = False
    st.session_state["user"] = None


def get_current_user() -> Optional[dict]:
    return st.session_state.get("user")


def is_logged_in() -> bool:
    return bool(st.session_state.get("logged_in", False))


def require_login() -> bool:
    init_auth_table()
    if is_logged_in():
        return True
    st.warning("請先登入後再使用系統功能。")
    st.stop()
    return False


def require_roles(roles: list[str]) -> bool:
    require_login()
    user = get_current_user() or {}
    if user.get("role") in roles:
        return True
    st.error("您目前沒有權限使用此頁面。")
    st.stop()
    return False


def get_users_df() -> pd.DataFrame:
    init_auth_table()
    with get_conn() as conn:
        return pd.read_sql(text("SELECT id, username, display_name, role, team, is_active, created_at, updated_at FROM users ORDER BY id ASC"), conn)


def create_user(username: str, password: str, display_name: str, role: str, team: str) -> None:
    init_auth_table()
    with get_conn() as conn:
        conn.execute(text("""
            INSERT INTO users (username, password_hash, display_name, role, team, is_active, created_at, updated_at)
            VALUES (:username, :password_hash, :display_name, :role, :team, 1, :created_at, :updated_at)
        """), {
            "username": username.strip(),
            "password_hash": hash_password(password),
            "display_name": display_name.strip(),
            "role": role,
            "team": team,
            "created_at": now_str(),
            "updated_at": now_str(),
        })


def update_user_status(user_id: int, is_active: int) -> None:
    init_auth_table()
    with get_conn() as conn:
        conn.execute(text("UPDATE users SET is_active = :is_active, updated_at = :updated_at WHERE id = :user_id"), {
            "is_active": is_active,
            "updated_at": now_str(),
            "user_id": user_id,
        })
