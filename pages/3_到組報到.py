import streamlit as st

from auth import get_current_user, require_login
from config import ARRIVAL_STATUS, GROUPS, SYSTEM_NAME
from db import get_arrivals, get_request_by_no, get_request_options, init_db, insert_arrival, now_tw
from utils import apply_style, combine_date_time, page_header, safe_dataframe, set_page_config, sidebar_user_panel

set_page_config("到組報到")
init_db()
apply_style()
require_login()

st.sidebar.title(SYSTEM_NAME)
sidebar_user_panel(get_current_user())

page_header("到組報到", "人員抵達支援組別後，請於此完成到組報到。")

request_options = get_request_options(active_only=True)
now = now_tw().replace(tzinfo=None)

with st.form("arrival_form", clear_on_submit=True):
    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input("姓名")
        origin_team = st.selectbox("原組別", GROUPS)
        request_no = st.selectbox("對應需求編號", options=request_options) if request_options else st.text_input("對應需求編號")

    with col2:
        arrival_team = st.selectbox("抵達組別", GROUPS)
        arrival_date = st.date_input("到組日期", value=now.date())
        arrival_time_input = st.time_input("到組時間", value=now.time().replace(microsecond=0))
        st.text_input("狀態", value=ARRIVAL_STATUS, disabled=True)

    submitted = st.form_submit_button("完成到組報到", use_container_width=True)

    if submitted:
        try:
            if not name.strip():
                st.error("請填寫姓名。")
            elif not request_no:
                st.error("請選擇對應需求編號。")
            else:
                request_info = get_request_by_no(request_no)
                if request_info and arrival_team != request_info["request_team"]:
                    st.warning("提醒：抵達組別與需求組別不同，請再次確認。")

                arrival_time = combine_date_time(arrival_date, arrival_time_input)
                insert_arrival(name.strip(), origin_team, arrival_team, arrival_time, request_no, ARRIVAL_STATUS)
                st.success(f"{name.strip()} 已完成到組報到。")
        except Exception as exc:
            st.error(f"到組報到失敗：{exc}")

df = get_arrivals()

with st.expander("查詢與篩選", expanded=True):
    col1, col2 = st.columns(2)
    origin_filter = col1.multiselect("原組別", options=sorted(df["origin_team"].unique().tolist()) if not df.empty else [])
    arrival_filter = col2.multiselect("抵達組別", options=sorted(df["arrival_team"].unique().tolist()) if not df.empty else [])
    keyword = st.text_input("關鍵字查詢（姓名 / 需求編號）")

filtered_df = df.copy()

if not filtered_df.empty:
    if origin_filter:
        filtered_df = filtered_df[filtered_df["origin_team"].isin(origin_filter)]
    if arrival_filter:
        filtered_df = filtered_df[filtered_df["arrival_team"].isin(arrival_filter)]
    if keyword.strip():
        mask = (
            filtered_df["name"].astype(str).str.contains(keyword, case=False, na=False)
            | filtered_df["request_no"].astype(str).str.contains(keyword, case=False, na=False)
        )
        filtered_df = filtered_df[mask]

safe_dataframe(filtered_df[["name", "origin_team", "arrival_team", "arrival_time", "request_no", "status"]] if not filtered_df.empty else filtered_df)
