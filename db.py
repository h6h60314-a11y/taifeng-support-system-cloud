import os
from contextlib import contextmanager
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from sqlalchemy import create_engine, text
from zoneinfo import ZoneInfo

from config import DB_PATH

TW_TZ = ZoneInfo("Asia/Taipei")

Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)


def now_tw() -> datetime:
    return datetime.now(TW_TZ)


def now_tw_str(fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    return now_tw().strftime(fmt)


def get_database_url() -> str:
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url

    try:
        import streamlit as st
        if "database" in st.secrets and "url" in st.secrets["database"]:
            return st.secrets["database"]["url"]
    except Exception:
        pass

    return f"sqlite:///{DB_PATH}"


@lru_cache(maxsize=1)
def get_engine():
    url = get_database_url()
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, future=True, pool_pre_ping=True, connect_args=connect_args)


@contextmanager
def get_conn():
    engine = get_engine()
    with engine.begin() as conn:
        yield conn


def init_db() -> None:
    engine = get_engine()
    is_postgres = engine.dialect.name == "postgresql"
    auto_id = "SERIAL PRIMARY KEY" if is_postgres else "INTEGER PRIMARY KEY AUTOINCREMENT"

    with get_conn() as conn:
        conn.execute(
            text(
                f"""
                CREATE TABLE IF NOT EXISTS support_requests (
                    id {auto_id},
                    request_no VARCHAR(50) NOT NULL UNIQUE,
                    request_team VARCHAR(100) NOT NULL,
                    publish_time VARCHAR(30) NOT NULL,
                    required_count INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    priority VARCHAR(10) NOT NULL,
                    note TEXT,
                    status VARCHAR(20) NOT NULL,
                    created_at VARCHAR(30) NOT NULL,
                    updated_at VARCHAR(30) NOT NULL
                )
                """
            )
        )

        conn.execute(
            text(
                f"""
                CREATE TABLE IF NOT EXISTS departures (
                    id {auto_id},
                    name VARCHAR(100) NOT NULL,
                    origin_team VARCHAR(100) NOT NULL,
                    target_team VARCHAR(100) NOT NULL,
                    depart_time VARCHAR(30) NOT NULL,
                    request_no VARCHAR(50) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    created_at VARCHAR(30) NOT NULL,
                    updated_at VARCHAR(30) NOT NULL
                )
                """
            )
        )

        conn.execute(
            text(
                f"""
                CREATE TABLE IF NOT EXISTS arrivals (
                    id {auto_id},
                    name VARCHAR(100) NOT NULL,
                    origin_team VARCHAR(100) NOT NULL,
                    arrival_team VARCHAR(100) NOT NULL,
                    arrival_time VARCHAR(30) NOT NULL,
                    request_no VARCHAR(50) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    created_at VARCHAR(30) NOT NULL,
                    updated_at VARCHAR(30) NOT NULL
                )
                """
            )
        )


def now_str() -> str:
    return now_tw_str()


def generate_request_no() -> str:
    today = now_tw().strftime("%Y%m%d")
    prefix = f"REQ{today}"
    with get_conn() as conn:
        count = conn.execute(
            text("SELECT COUNT(*) FROM support_requests WHERE request_no LIKE :prefix"),
            {"prefix": f"{prefix}%"},
        ).scalar_one()
    return f"{prefix}{count + 1:03d}"


def insert_support_request(
    request_no: str,
    request_team: str,
    publish_time: str,
    required_count: int,
    reason: str,
    priority: str,
    note: str,
    status: str,
) -> None:
    ts = now_str()
    with get_conn() as conn:
        conn.execute(
            text(
                """
                INSERT INTO support_requests
                (request_no, request_team, publish_time, required_count, reason, priority, note, status, created_at, updated_at)
                VALUES (:request_no, :request_team, :publish_time, :required_count, :reason, :priority, :note, :status, :created_at, :updated_at)
                """
            ),
            {
                "request_no": request_no,
                "request_team": request_team,
                "publish_time": publish_time,
                "required_count": required_count,
                "reason": reason,
                "priority": priority,
                "note": note,
                "status": status,
                "created_at": ts,
                "updated_at": ts,
            },
        )


def insert_departure(
    name: str,
    origin_team: str,
    target_team: str,
    depart_time: str,
    request_no: str,
    status: str,
) -> None:
    ts = now_str()
    with get_conn() as conn:
        conn.execute(
            text(
                """
                INSERT INTO departures
                (name, origin_team, target_team, depart_time, request_no, status, created_at, updated_at)
                VALUES (:name, :origin_team, :target_team, :depart_time, :request_no, :status, :created_at, :updated_at)
                """
            ),
            {
                "name": name,
                "origin_team": origin_team,
                "target_team": target_team,
                "depart_time": depart_time,
                "request_no": request_no,
                "status": status,
                "created_at": ts,
                "updated_at": ts,
            },
        )

        conn.execute(
            text(
                "UPDATE support_requests SET status = '支援中', updated_at = :updated_at "
                "WHERE request_no = :request_no AND status = '待支援'"
            ),
            {"updated_at": ts, "request_no": request_no},
        )


def insert_arrival(
    name: str,
    origin_team: str,
    arrival_team: str,
    arrival_time: str,
    request_no: str,
    status: str,
) -> None:
    ts = now_str()
    with get_conn() as conn:
        conn.execute(
            text(
                """
                INSERT INTO arrivals
                (name, origin_team, arrival_team, arrival_time, request_no, status, created_at, updated_at)
                VALUES (:name, :origin_team, :arrival_team, :arrival_time, :request_no, :status, :created_at, :updated_at)
                """
            ),
            {
                "name": name,
                "origin_team": origin_team,
                "arrival_team": arrival_team,
                "arrival_time": arrival_time,
                "request_no": request_no,
                "status": status,
                "created_at": ts,
                "updated_at": ts,
            },
        )
        auto_update_request_status(request_no, conn)


def auto_update_request_status(request_no: str, conn=None) -> None:
    own_conn = False
    if conn is None:
        own_conn = True
        cm = get_conn()
        conn = cm.__enter__()

    req = conn.execute(
        text("SELECT required_count FROM support_requests WHERE request_no = :request_no"),
        {"request_no": request_no},
    ).fetchone()

    if req:
        arrived_count = conn.execute(
            text("SELECT COUNT(*) FROM arrivals WHERE request_no = :request_no"),
            {"request_no": request_no},
        ).scalar_one()

        new_status = "已補足" if arrived_count >= req[0] else "支援中"

        conn.execute(
            text(
                "UPDATE support_requests SET status = :status, updated_at = :updated_at "
                "WHERE request_no = :request_no"
            ),
            {
                "status": new_status,
                "updated_at": now_str(),
                "request_no": request_no,
            },
        )

    if own_conn:
        cm.__exit__(None, None, None)


def fetch_df(query: str, params: Optional[dict[str, Any]] = None) -> pd.DataFrame:
    with get_engine().connect() as conn:
        return pd.read_sql(text(query), conn, params=params or {})


def get_requests() -> pd.DataFrame:
    return fetch_df("SELECT * FROM support_requests ORDER BY publish_time DESC, id DESC")


def get_departures() -> pd.DataFrame:
    return fetch_df("SELECT * FROM departures ORDER BY depart_time DESC, id DESC")


def get_arrivals() -> pd.DataFrame:
    return fetch_df("SELECT * FROM arrivals ORDER BY arrival_time DESC, id DESC")


def get_dashboard_data() -> dict[str, Any]:
    today = now_tw().strftime("%Y-%m-%d")

    requests_df = fetch_df(
        "SELECT * FROM support_requests WHERE substr(publish_time, 1, 10) = :today ORDER BY publish_time DESC",
        {"today": today},
    )
    departures_df = get_departures()
    arrivals_df = get_arrivals()

    if departures_df.empty:
        pending_arrival_df = departures_df.copy()
    else:
        merged = departures_df.merge(
            arrivals_df[["name", "request_no", "arrival_time"]],
            on=["name", "request_no"],
            how="left",
        )
        pending_arrival_df = merged[merged["arrival_time"].isna()].copy()

    waiting_requests = requests_df[requests_df["status"] == "待支援"] if not requests_df.empty else requests_df
    arrived_today = arrivals_df[arrivals_df["arrival_time"].str.startswith(today)] if not arrivals_df.empty else arrivals_df

    return {
        "today_requests": len(requests_df),
        "waiting_teams": waiting_requests["request_team"].drop_duplicates().tolist() if not waiting_requests.empty else [],
        "pending_arrival_count": len(pending_arrival_df),
        "arrived_count": len(arrived_today),
        "pending_arrival_df": pending_arrival_df,
        "requests_df": requests_df,
        "departures_df": departures_df,
        "arrivals_df": arrivals_df,
    }


def get_unarrived_supporters() -> pd.DataFrame:
    departures_df = get_departures()
    arrivals_df = get_arrivals()

    if departures_df.empty:
        return departures_df

    merged = departures_df.merge(
        arrivals_df[["name", "request_no", "arrival_time"]],
        on=["name", "request_no"],
        how="left",
    )
    return merged[merged["arrival_time"].isna()].copy()


def get_completed_supporters() -> pd.DataFrame:
    return fetch_df(
        """
        SELECT a.*, r.status AS request_status
        FROM arrivals a
        LEFT JOIN support_requests r ON a.request_no = r.request_no
        WHERE r.status = '已補足'
        ORDER BY a.arrival_time DESC
        """
    )


def get_request_options(active_only: bool = False) -> list[str]:
    query = "SELECT request_no FROM support_requests"
    if active_only:
        query += " WHERE status IN ('待支援', '支援中')"
    query += " ORDER BY request_no DESC"

    df = fetch_df(query)
    return df["request_no"].tolist() if not df.empty else []


def get_request_by_no(request_no: str) -> Optional[dict[str, Any]]:
    df = fetch_df(
        "SELECT * FROM support_requests WHERE request_no = :request_no",
        {"request_no": request_no},
    )
    return None if df.empty else df.iloc[0].to_dict()


def update_request_status(request_no: str, status: str) -> None:
    with get_conn() as conn:
        conn.execute(
            text(
                "UPDATE support_requests SET status = :status, updated_at = :updated_at "
                "WHERE request_no = :request_no"
            ),
            {
                "status": status,
                "updated_at": now_str(),
                "request_no": request_no,
            },
        )


def update_table_by_id(table_name: str, row_id: int, field_values: dict[str, Any]) -> None:
    allowed_tables = {"support_requests", "departures", "arrivals"}
    if table_name not in allowed_tables:
        raise ValueError("不支援的資料表")

    clean_data = {k: v for k, v in field_values.items() if k not in {"id", "created_at", "updated_at"}}
    clean_data["updated_at"] = now_str()
    set_clause = ", ".join([f"{k} = :{k}" for k in clean_data.keys()])
    clean_data["row_id"] = row_id

    with get_conn() as conn:
        conn.execute(text(f"UPDATE {table_name} SET {set_clause} WHERE id = :row_id"), clean_data)

        if table_name in {"arrivals", "support_requests"}:
            row = conn.execute(
                text(f"SELECT request_no FROM {table_name} WHERE id = :row_id"),
                {"row_id": row_id},
            ).fetchone()
            if row and row[0]:
                auto_update_request_status(row[0], conn)


def delete_table_by_id(table_name: str, row_id: int) -> None:
    allowed_tables = {"support_requests", "departures", "arrivals"}
    if table_name not in allowed_tables:
        raise ValueError("不支援的資料表")

    request_no = None
    with get_conn() as conn:
        row = conn.execute(
            text(f"SELECT request_no FROM {table_name} WHERE id = :row_id"),
            {"row_id": row_id},
        ).fetchone()

        if row:
            request_no = row[0]

        conn.execute(
            text(f"DELETE FROM {table_name} WHERE id = :row_id"),
            {"row_id": row_id},
        )

        if request_no:
            auto_update_request_status(request_no, conn)
