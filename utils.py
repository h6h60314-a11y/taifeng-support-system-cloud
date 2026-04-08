from datetime import datetime

import pandas as pd
import streamlit as st

from config import ALERT_MINUTES, SYSTEM_NAME


def set_page_config(page_title: str) -> None:
    st.set_page_config(
        page_title=f"{SYSTEM_NAME}｜{page_title}",
        page_icon="🏢",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def apply_style() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top right, rgba(29,95,151,0.10), transparent 22%),
                linear-gradient(180deg, #f4f7fb 0%, #eef3f8 100%);
        }
        .main .block-container {
            padding-top: 1.2rem;
            padding-bottom: 2rem;
        }
        .tf-title {
            padding: 1.2rem 1.35rem;
            border-radius: 18px;
            background: linear-gradient(135deg, #0b2944 0%, #1d5f97 62%, #2c7cc1 100%);
            color: white;
            margin-bottom: 1rem;
            box-shadow: 0 10px 26px rgba(16, 53, 87, 0.18);
            border: 1px solid rgba(255,255,255,0.08);
        }
        .tf-card {
            background: white;
            border: 1px solid #dbe5ef;
            border-radius: 16px;
            padding: 1rem 1.05rem;
            box-shadow: 0 4px 14px rgba(15, 53, 87, 0.06);
            height: 100%;
        }
        .tf-portal-card {
            background: rgba(255,255,255,0.97);
            border: 1px solid #dbe5ef;
            border-radius: 18px;
            padding: 1.1rem 1.15rem;
            box-shadow: 0 8px 22px rgba(15, 53, 87, 0.07);
        }
        .tf-alert {
            background: #fff4e5;
            border-left: 6px solid #f59e0b;
            padding: 0.9rem 1rem;
            border-radius: 10px;
            color: #7c4a03;
            margin-bottom: 0.8rem;
        }
        .tf-danger {
            background: #fff1f2;
            border-left: 6px solid #e11d48;
            padding: 0.9rem 1rem;
            border-radius: 10px;
            color: #881337;
            margin-bottom: 0.8rem;
        }
        .tf-badge {
            display:inline-block;
            padding:0.3rem 0.65rem;
            border-radius:999px;
            background:#dbeafe;
            color:#1d4ed8;
            font-size:0.82rem;
            font-weight:600;
        }
        div[data-testid="stMetric"] {
            background: white;
            border: 1px solid #dbe5ef;
            padding: 0.8rem;
            border-radius: 14px;
            box-shadow: 0 4px 14px rgba(15, 53, 87, 0.05);
        }
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0c2f4c 0%, #163f64 100%);
        }
        section[data-testid="stSidebar"] * {
            color: white !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, desc: str) -> None:
    st.markdown(
        f"""
        <div class="tf-title">
            <h2 style="margin:0;">{title}</h2>
            <div style="margin-top:0.35rem; font-size:0.96rem; opacity:0.95;">{desc}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def portal_card(title: str, desc: str, badge: str = "") -> None:
    badge_html = f'<div class="tf-badge">{badge}</div>' if badge else ""
    st.markdown(
        f"""
        <div class="tf-portal-card">
            {badge_html}
            <h4 style="margin:0.5rem 0 0.35rem 0; color:#0f3557;">{title}</h4>
            <div style="color:#475569; line-height:1.65;">{desc}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_datetime_for_input(dt_str: str):
    try:
        return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return datetime.now()


def combine_date_time(date_value, time_value) -> str:
    return datetime.combine(date_value, time_value).strftime("%Y-%m-%d %H:%M:%S")


def abnormal_pending_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    result = df.copy()
    result["depart_time_dt"] = pd.to_datetime(result["depart_time"], errors="coerce")
    result["等待分鐘"] = ((pd.Timestamp.now() - result["depart_time_dt"]).dt.total_seconds() / 60).fillna(0).astype(int)
    return result[result["等待分鐘"] > ALERT_MINUTES].sort_values("等待分鐘", ascending=False)


def safe_dataframe(df: pd.DataFrame, use_container_width: bool = True) -> None:
    if df is None or df.empty:
        st.info("目前沒有資料。")
        return
    st.dataframe(df, use_container_width=use_container_width, hide_index=True)


def sidebar_user_panel(user: dict | None) -> None:
    if not user:
        return
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**登入者：** {user.get('display_name', '-')}")
    st.sidebar.markdown(f"**角色：** {user.get('role', '-')}")
    st.sidebar.markdown(f"**所屬組別：** {user.get('team', '-')}")
