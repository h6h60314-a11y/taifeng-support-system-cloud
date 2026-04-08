from pathlib import Path

import streamlit as st

from auth import get_current_user, init_auth_table, is_logged_in, login, logout
from config import SYSTEM_NAME
from db import get_dashboard_data, init_db
from utils import (
    abnormal_pending_df,
    apply_style,
    page_header,
    portal_card,
    safe_dataframe,
    set_page_config,
    sidebar_user_panel,
)

set_page_config("企業入口首頁")
init_db()
init_auth_table()
apply_style()

BASE_DIR = Path(__file__).parent


def render_home():
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
        st.code("admin / admin123\nsupervisor / supervisor123\nstaff01 / staff123")
        st.stop()

    user = get_current_user() or {}
    data = get_dashboard_data()
    abnormal_df = abnormal_pending_df(data["pending_arrival_df"])
    waiting_df = (
        data["requests_df"][data["requests_df"]["status"] == "待支援"]
        if not data["requests_df"].empty
        else data["requests_df"]
    )

    st.markdown('<div class="dispatch-subtitle">即時缺口提示</div>', unsafe_allow_html=True)
    if waiting_df.empty:
        st.success("目前沒有待支援缺口。")
    else:
        alert_df = (
            waiting_df.groupby("request_team", as_index=False)["required_count"]
            .sum()
            .sort_values("required_count", ascending=False)
            .head(2)
        )
        alert_cols = st.columns(len(alert_df) if len(alert_df) > 1 else 1)
        for i, (_, row) in enumerate(alert_df.iterrows()):
            with alert_cols[i]:
                st.markdown(
                    f'''
                    <div class="dispatch-alert-card">
                        <div class="dispatch-alert-left">
                            <div class="dispatch-alert-num">+{int(row['required_count'])}</div>
                            <div class="dispatch-alert-team">{row['request_team']}</div>
                        </div>
                        <div class="dispatch-alert-action">立即派員</div>
                    </div>
                    ''',
                    unsafe_allow_html=True,
                )

    st.markdown('<div class="dispatch-board">', unsafe_allow_html=True)
    st.markdown('<div class="dispatch-board-header">• 支援調度系統</div>', unsafe_allow_html=True)
    st.markdown(
    '''
    <div class="dispatch-main-panel">
        <div class="dispatch-main-icon">＋</div>
        <div>
            <div class="dispatch-main-title">發起人力調派</div>
            <div class="dispatch-main-sub">START DISPATCH PROTOCOL</div>
        </div>
    </div>
    ''',
    unsafe_allow_html=True,
   )
   st.caption("請由左側功能選單進入「支援需求發布」。")
   st.markdown('</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f'<div class="status-head status-yellow">● 去程在途（{data["pending_arrival_count"]}）</div>',
            unsafe_allow_html=True,
        )
        if data["pending_arrival_df"].empty:
            st.markdown('<div class="status-box">目前無紀錄</div>', unsafe_allow_html=True)
        else:
            show = data["pending_arrival_df"][["name", "target_team", "request_no"]].head(5)
            st.dataframe(show, use_container_width=True, hide_index=True)

    with c2:
        st.markdown(
            f'<div class="status-head status-green">● 駐組支援（{data["arrived_count"]}）</div>',
            unsafe_allow_html=True,
        )
        if data["arrivals_df"].empty:
            st.markdown('<div class="status-box">目前無紀錄</div>', unsafe_allow_html=True)
        else:
            show = data["arrivals_df"][["name", "arrival_team", "request_no"]].head(5)
            st.dataframe(show, use_container_width=True, hide_index=True)

    with c3:
        st.markdown(
            f'<div class="status-head status-blue">● 調派進中（{len(abnormal_df)}）</div>',
            unsafe_allow_html=True,
        )
        if abnormal_df.empty:
            st.markdown('<div class="status-box">目前無紀錄</div>', unsafe_allow_html=True)
        else:
            show = abnormal_df[["name", "target_team", "等待分鐘"]].head(5)
            st.dataframe(show, use_container_width=True, hide_index=True)

    metric_cols = st.columns(5)
    metric_cols[0].metric("今日支援需求總數", data["today_requests"])
    metric_cols[1].metric("待支援組別", len(data["waiting_teams"]))
    metric_cols[2].metric("已離組未到組", data["pending_arrival_count"])
    metric_cols[3].metric("已到組人數", data["arrived_count"])
    metric_cols[4].metric("異常提醒", len(abnormal_df))

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
                f"目前登入者：{user.get('display_name', '-')}\n角色：{user.get('role', '-')}\n所屬組別：{user.get('team', '-')}",
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
            "- 一般人員：可進行離組簽退、到組報到、查詢資料。\n"
            "- 主管：可查看主管即時總表與整體狀況。\n"
            "- 管理員：可維護帳號與權限。"
        )


pages = {
    "系統功能": [
        st.Page(render_home, title="首頁 Dashboard", icon="🏠", default=True),
        st.Page("pages/1_支援需求發布.py", title="支援需求發布", icon="📝"),
        st.Page("pages/2_離組簽退.py", title="離組簽退", icon="🚶"),
        st.Page("pages/3_到組報到.py", title="到組報到", icon="✅"),
        st.Page("pages/4_主管即時總表.py", title="主管即時總表", icon="📊"),
        st.Page("pages/5_資料查詢與編輯.py", title="資料查詢與編輯", icon="🗂️"),
    ],
    "管理功能": [
        st.Page("pages/6_帳號與權限管理.py", title="帳號與權限管理", icon="🔐"),
    ],
}

pg = st.navigation(pages, position="sidebar")
pg.run()
