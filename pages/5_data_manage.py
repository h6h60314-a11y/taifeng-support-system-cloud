import streamlit as st

from auth import get_current_user, require_roles
from config import REQUEST_STATUSES, SYSTEM_NAME
from db import delete_table_by_id, get_arrivals, get_departures, get_requests, init_db, update_table_by_id
from utils import apply_style, format_datetime_for_input, page_header, safe_dataframe, set_page_config, sidebar_user_panel

set_page_config("資料查詢與編輯")
init_db()
apply_style()
require_roles(["admin", "supervisor"])
st.sidebar.title(SYSTEM_NAME)
sidebar_user_panel(get_current_user())
page_header("資料查詢與編輯", "所有資料可查詢、可篩選、可編輯，適合主管後續修正。")

table_option = st.selectbox("選擇資料類型", ["支援需求", "離組簽退", "到組報到"])
if table_option == "支援需求":
    table_name = "support_requests"; df = get_requests(); display_cols = ["id", "request_no", "request_team", "publish_time", "required_count", "reason", "priority", "note", "status"]
elif table_option == "離組簽退":
    table_name = "departures"; df = get_departures(); display_cols = ["id", "name", "origin_team", "target_team", "depart_time", "request_no", "status"]
else:
    table_name = "arrivals"; df = get_arrivals(); display_cols = ["id", "name", "origin_team", "arrival_team", "arrival_time", "request_no", "status"]
keyword = st.text_input("關鍵字查詢")
filtered_df = df.copy()
if not filtered_df.empty and keyword.strip():
    mask = filtered_df.astype(str).apply(lambda s: s.str.contains(keyword, case=False, na=False))
    filtered_df = filtered_df[mask.any(axis=1)]
st.subheader("目前資料")
safe_dataframe(filtered_df[display_cols] if not filtered_df.empty else filtered_df)
st.subheader("單筆編輯")
if filtered_df.empty:
    st.info("目前沒有可編輯資料。")
else:
    row_id = st.selectbox("選擇要編輯的 ID", options=filtered_df["id"].tolist())
    row = filtered_df[filtered_df["id"] == row_id].iloc[0]
    with st.form("edit_form"):
        update_data = {}
        if table_name == "support_requests":
            st.text_input("需求編號", value=row["request_no"], disabled=True)
            update_data["request_team"] = st.text_input("需求組別", value=row["request_team"])
            dt = format_datetime_for_input(row["publish_time"])
            c1, c2 = st.columns(2)
            date_val = c1.date_input("發布日期", value=dt.date())
            time_val = c2.time_input("發布時間", value=dt.time())
            update_data["publish_time"] = f"{date_val} {time_val.strftime('%H:%M:%S')}"
            update_data["required_count"] = st.number_input("需求人數", min_value=1, value=int(row["required_count"]))
            update_data["reason"] = st.text_area("支援原因", value=row["reason"])
            update_data["priority"] = st.selectbox("優先等級", ["高", "中", "低"], index=["高", "中", "低"].index(row["priority"]) if row["priority"] in ["高", "中", "低"] else 1)
            update_data["note"] = st.text_area("備註", value=row["note"] if row["note"] else "")
            update_data["status"] = st.selectbox("狀態", REQUEST_STATUSES, index=REQUEST_STATUSES.index(row["status"]) if row["status"] in REQUEST_STATUSES else 0)
        elif table_name == "departures":
            update_data["name"] = st.text_input("姓名", value=row["name"])
            update_data["origin_team"] = st.text_input("原組別", value=row["origin_team"])
            update_data["target_team"] = st.text_input("前往支援組別", value=row["target_team"])
            dt = format_datetime_for_input(row["depart_time"])
            c1, c2 = st.columns(2)
            date_val = c1.date_input("離組日期", value=dt.date())
            time_val = c2.time_input("離組時間", value=dt.time())
            update_data["depart_time"] = f"{date_val} {time_val.strftime('%H:%M:%S')}"
            update_data["request_no"] = st.text_input("對應需求編號", value=row["request_no"])
            update_data["status"] = st.text_input("狀態", value=row["status"])
        else:
            update_data["name"] = st.text_input("姓名", value=row["name"])
            update_data["origin_team"] = st.text_input("原組別", value=row["origin_team"])
            update_data["arrival_team"] = st.text_input("抵達組別", value=row["arrival_team"])
            dt = format_datetime_for_input(row["arrival_time"])
            c1, c2 = st.columns(2)
            date_val = c1.date_input("到組日期", value=dt.date())
            time_val = c2.time_input("到組時間", value=dt.time())
            update_data["arrival_time"] = f"{date_val} {time_val.strftime('%H:%M:%S')}"
            update_data["request_no"] = st.text_input("對應需求編號", value=row["request_no"])
            update_data["status"] = st.text_input("狀態", value=row["status"])
        c1, c2 = st.columns(2)
        save_clicked = c1.form_submit_button("儲存修改", use_container_width=True)
        delete_clicked = c2.form_submit_button("刪除此筆", use_container_width=True)
        if save_clicked:
            try:
                update_table_by_id(table_name, int(row_id), update_data)
                st.success("資料更新成功。")
                st.rerun()
            except Exception as exc:
                st.error(f"更新失敗：{exc}")
        if delete_clicked:
            try:
                delete_table_by_id(table_name, int(row_id))
                st.success("資料已刪除。")
                st.rerun()
            except Exception as exc:
                st.error(f"刪除失敗：{exc}")
