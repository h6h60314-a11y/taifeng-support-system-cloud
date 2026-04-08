from db import init_db, get_dashboard_data
from auth import get_current_user, init_auth_table, is_logged_in, login, logout
from config import SYSTEM_NAME
from utils import (
    abnormal_pending_df,
    apply_style,
    page_header,
    portal_card,
    safe_dataframe,
    set_page_config,
    sidebar_user_panel,
)
import streamlit as st


set_page_config("企業入口首頁")
init_db()
init_auth_table()
apply_style()

st.sidebar.title(SYSTEM_NAME)
st.sidebar.caption("GF Logistics Support Portal")

user = get_current_user()
if is_logged_in() and user:
    sidebar_user_panel(user)
    if st.sidebar.button("登出系統", use_container_width=True):
        logout()
        st.rerun()
else:
    with st.sidebar.form("login_form"):
        st.subheader("系統登入")
        username = st.text_input("帳號")
        password = st.text_input("密碼", type="password")
        submitted = st.form_submit_button("登入", use_container_width=True)
        if submitted:
            if login(username, password):
                st.success("登入成功")
                st.rerun()
            else:
                st.error("帳號或密碼錯誤")

page_header("大豐物流部－支援系統", "企業內部支援調度平台｜支援需求發布、離到組控管、主管即時掌握")

if not is_logged_in():
    c1, c2, c3 = st.columns(3)
    with c1:
        portal_card("支援需求發布", "各組可建立支援需求，系統自動產生唯一需求編號。", "需求管理")
    with c2:
        portal_card("離組簽退 / 到組報到", "人員移動可即時登錄，主管能立即掌握支援流向。", "人員流向")
    with c3:
        portal_card("主管即時總表", "集中查看待支援、支援中、異常提醒與整體統計。", "主管監控")

    st.info("請先於左側輸入帳號密碼登入。登入後即可使用完整功能。")
    st.subheader("預設測試帳號")
    st.code(
        "admin / admin123\n"
        "supervisor / supervisor123\n"
        "staff01 / staff123"
    )
    st.stop()

user = get_current_user() or {}
page_links = st.columns(5)
with page_links[0]:
    st.page_link("pages/1_支援需求發布.py", label="支援需求發布", icon="📝")
with page_links[1]:
    st.page_link("pages/2_離組簽退.py", label="離組簽退", icon="🚶")
with page_links[2]:
    st.page_link("pages/3_到組報到.py", label="到組報到", icon="✅")
with page_links[3]:
    st.page_link("pages/4_主管即時總表.py", label="主管即時總表", icon="📊")
with page_links[4]:
    st.page_link("pages/5_資料查詢與編輯.py", label="資料查詢與編輯", icon="🗂️")

if user.get("role") == "admin":
    st.page_link("pages/6_帳號與權限管理.py", label="帳號與權限管理", icon="🔐")

data = get_dashboard_data()
abnormal_df = abnormal_pending_df(data["pending_arrival_df"])

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("今日支援需求總數", data["today_requests"])
col2.metric("待支援組別", len(data["waiting_teams"]))
col3.metric("已離組未到組", data["pending_arrival_count"])
col4.metric("已到組人數", data["arrived_count"])
col5.metric("異常提醒", len(abnormal_df))

left, right = st.columns([1.2, 1])
with left:
    st.subheader("今日待辦焦點")
    a, b = st.columns(2)
    with a:
        portal_card(
            "待支援組別",
            "、".join(data["waiting_teams"]) if data["waiting_teams"] else "目前沒有待支援組別。",
            "今日重點",
        )
    with b:
        portal_card(
            "登入角色",
            f"目前登入者：{user.get('display_name', '-') }\n角色：{user.get('role', '-') }\n所屬組別：{user.get('team', '-') }",
            "使用者資訊",
        )

    st.subheader("今日支援需求")
    request_cols = ["request_no", "request_team", "publish_time", "required_count", "priority", "status"]
    safe_dataframe(data["requests_df"][request_cols] if not data["requests_df"].empty else data["requests_df"])

with right:
    st.subheader("異常提醒")
    if abnormal_df.empty:
        st.success("目前沒有超時未到組異常。")
    else:
        for _, row in abnormal_df.iterrows():
            st.markdown(
                f'<div class="tf-danger"><b>{row["name"]}</b>｜{row["origin_team"]} → {row["target_team"]}<br>需求編號：{row["request_no"]}<br>已等待 {row["等待分鐘"]} 分鐘，尚未到組。</div>',
                unsafe_allow_html=True,
            )

    st.subheader("入口說明")
    st.markdown(
        """
        - 一般人員：可進行離組簽退、到組報到、查詢資料。
        - 主管：可查看主管即時總表與整體狀況。
        - 管理員：可維護帳號與權限。
        """
    )

st.subheader("已離組未到組名單")
pending_cols = ["name", "origin_team", "target_team", "depart_time", "request_no", "status"]
safe_dataframe(data["pending_arrival_df"][pending_cols] if not data["pending_arrival_df"].empty else data["pending_arrival_df"])
