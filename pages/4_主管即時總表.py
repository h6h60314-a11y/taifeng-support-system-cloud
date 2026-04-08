import pandas as pd
import streamlit as st

from auth import get_current_user, require_roles
from config import SYSTEM_NAME
from db import get_arrivals, get_completed_supporters, get_dashboard_data, get_requests, get_unarrived_supporters, init_db, update_request_status
from utils import abnormal_pending_df, apply_style, page_header, safe_dataframe, set_page_config, sidebar_user_panel

set_page_config("主管即時總表")
init_db()
apply_style()
require_roles(["admin", "supervisor"])
st.sidebar.title(SYSTEM_NAME)
sidebar_user_panel(get_current_user())
page_header("主管即時總表", "主管可即時查看支援需求、離到組狀況與各組統計。")

data = get_dashboard_data()
requests_df = get_requests()
unarrived_df = get_unarrived_supporters()
arrivals_df = get_arrivals()
completed_people_df = get_completed_supporters()
col1, col2, col3, col4 = st.columns(4)
col1.metric("待支援需求", len(requests_df[requests_df["status"] == "待支援"]) if not requests_df.empty else 0)
col2.metric("支援中需求", len(requests_df[requests_df["status"] == "支援中"]) if not requests_df.empty else 0)
col3.metric("已離組未到組", len(unarrived_df))
col4.metric("已到組人員", len(arrivals_df))

st.subheader("需求狀態快速更新")
active_requests = requests_df[["request_no", "request_team", "required_count", "status"]].copy() if not requests_df.empty else pd.DataFrame()
if active_requests.empty:
    st.info("目前沒有需求資料。")
else:
    selected_req = st.selectbox("選擇需求編號", options=active_requests["request_no"].tolist())
    current_row = active_requests[active_requests["request_no"] == selected_req].iloc[0]
    col_a, col_b, col_c = st.columns([1.2, 1, 1])
    col_a.write(f"目前組別：{current_row['request_team']}｜需求人數：{current_row['required_count']}")
    new_status = col_b.selectbox("更新狀態", options=["待支援", "支援中", "已補足"], index=["待支援", "支援中", "已補足"].index(current_row["status"]))
    if col_c.button("更新需求狀態", use_container_width=True):
        try:
            update_request_status(selected_req, new_status)
            st.success(f"需求 {selected_req} 狀態已更新為 {new_status}。")
            st.rerun()
        except Exception as exc:
            st.error(f"更新失敗：{exc}")

st.subheader("待支援需求清單")
safe_dataframe(requests_df[requests_df["status"] == "待支援"][ ["request_no", "request_team", "publish_time", "required_count", "priority", "reason", "status"] ] if not requests_df.empty else requests_df)
st.subheader("支援中需求清單")
safe_dataframe(requests_df[requests_df["status"] == "支援中"][ ["request_no", "request_team", "publish_time", "required_count", "priority", "reason", "status"] ] if not requests_df.empty else requests_df)
st.subheader("已離組未到組人員")
unarrived_show = unarrived_df[["name", "origin_team", "target_team", "depart_time", "request_no", "status"]] if not unarrived_df.empty else unarrived_df
safe_dataframe(unarrived_show)
abnormal_df = abnormal_pending_df(unarrived_df)
if not abnormal_df.empty:
    st.warning("以下人員已超過設定時間仍未到組：")
    safe_dataframe(abnormal_df[["name", "origin_team", "target_team", "depart_time", "request_no", "等待分鐘"]])
st.subheader("已到組人員")
safe_dataframe(arrivals_df[["name", "origin_team", "arrival_team", "arrival_time", "request_no", "status"]] if not arrivals_df.empty else arrivals_df)
st.subheader("支援完成人員")
safe_dataframe(completed_people_df[["name", "origin_team", "arrival_team", "arrival_time", "request_no", "status"]] if not completed_people_df.empty else completed_people_df)
st.subheader("各組別目前需求狀態統計")
if requests_df.empty:
    st.info("目前沒有統計資料。")
else:
    stat_df = requests_df.groupby(["request_team", "status"]).size().reset_index(name="筆數").pivot(index="request_team", columns="status", values="筆數").fillna(0).reset_index()
    safe_dataframe(stat_df)
