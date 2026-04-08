from datetime import datetime

import streamlit as st

from auth import get_current_user, require_login
from config import GROUPS, PRIORITIES, REQUEST_STATUSES, SYSTEM_NAME
from db import generate_request_no, get_requests, init_db, insert_support_request
from utils import apply_style, combine_date_time, page_header, safe_dataframe, set_page_config, sidebar_user_panel

set_page_config("支援需求發布")
init_db()
apply_style()
require_login()
st.sidebar.title(SYSTEM_NAME)
sidebar_user_panel(get_current_user())
page_header("支援需求發布", "建立各組支援需求，系統自動產生唯一需求編號。")

with st.form("support_request_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    request_no = generate_request_no()
    with col1:
        st.text_input("需求編號（自動生成）", value=request_no, disabled=True)
        request_team = st.selectbox("需求組別", GROUPS)
        publish_date = st.date_input("發布日期", value=datetime.now().date())
        required_count = st.number_input("需求人數", min_value=1, max_value=50, value=1, step=1)
    with col2:
        publish_time_input = st.time_input("發布時間", value=datetime.now().time())
        priority = st.selectbox("優先等級", PRIORITIES, index=1)
        status = st.selectbox("狀態", REQUEST_STATUSES, index=0)
    reason = st.text_area("支援原因", placeholder="請輸入支援原因")
    note = st.text_area("備註", placeholder="可填寫補充說明")
    submitted = st.form_submit_button("送出需求", use_container_width=True)
    if submitted:
        try:
            if not reason.strip():
                st.error("請填寫支援原因。")
            else:
                publish_time = combine_date_time(publish_date, publish_time_input)
                insert_support_request(request_no, request_team, publish_time, int(required_count), reason.strip(), priority, note.strip(), status)
                st.success(f"需求建立成功，需求編號：{request_no}")
        except Exception as exc:
            st.error(f"建立需求失敗：{exc}")

st.subheader("需求清單")
requests_df = get_requests()
with st.expander("查詢與篩選", expanded=True):
    col1, col2, col3 = st.columns(3)
    team_filter = col1.multiselect("需求組別", options=sorted(requests_df["request_team"].unique().tolist()) if not requests_df.empty else [])
    status_filter = col2.multiselect("狀態", options=sorted(requests_df["status"].unique().tolist()) if not requests_df.empty else [])
    priority_filter = col3.multiselect("優先等級", options=sorted(requests_df["priority"].unique().tolist()) if not requests_df.empty else [])
    keyword = st.text_input("關鍵字查詢（需求編號 / 原因 / 備註）")
filtered_df = requests_df.copy()
if not filtered_df.empty:
    if team_filter:
        filtered_df = filtered_df[filtered_df["request_team"].isin(team_filter)]
    if status_filter:
        filtered_df = filtered_df[filtered_df["status"].isin(status_filter)]
    if priority_filter:
        filtered_df = filtered_df[filtered_df["priority"].isin(priority_filter)]
    if keyword.strip():
        mask = filtered_df["request_no"].astype(str).str.contains(keyword, case=False, na=False) | filtered_df["reason"].astype(str).str.contains(keyword, case=False, na=False) | filtered_df["note"].astype(str).str.contains(keyword, case=False, na=False)
        filtered_df = filtered_df[mask]
safe_dataframe(filtered_df[["request_no", "request_team", "publish_time", "required_count", "reason", "priority", "note", "status"]] if not filtered_df.empty else filtered_df)
