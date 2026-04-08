import streamlit as st

from auth import create_user, get_current_user, get_users_df, require_roles, update_user_status
from config import GROUPS, SYSTEM_NAME
from utils import apply_style, page_header, safe_dataframe, set_page_config, sidebar_user_panel

set_page_config("帳號與權限管理")
apply_style()
require_roles(["admin"])
st.sidebar.title(SYSTEM_NAME)
sidebar_user_panel(get_current_user())
page_header("帳號與權限管理", "僅限系統管理員使用，可建立帳號並控管是否啟用。")

with st.form("create_user_form", clear_on_submit=True):
    c1, c2 = st.columns(2)
    username = c1.text_input("登入帳號")
    password = c2.text_input("登入密碼", type="password")
    display_name = c1.text_input("顯示名稱")
    role = c2.selectbox("角色", ["admin", "supervisor", "staff"])
    team = st.selectbox("所屬組別", GROUPS)
    submitted = st.form_submit_button("建立新帳號", use_container_width=True)
    if submitted:
        try:
            if not username.strip() or not password.strip() or not display_name.strip():
                st.error("請完整填寫帳號資料。")
            else:
                create_user(username, password, display_name, role, team)
                st.success("帳號建立成功。")
                st.rerun()
        except Exception as exc:
            st.error(f"建立帳號失敗：{exc}")

users_df = get_users_df()
st.subheader("帳號清單")
safe_dataframe(users_df)
if not users_df.empty:
    st.subheader("帳號啟用 / 停用")
    user_id = st.selectbox("選擇使用者 ID", options=users_df["id"].tolist())
    current_row = users_df[users_df["id"] == user_id].iloc[0]
    target_status = st.selectbox("設定狀態", options=[1, 0], format_func=lambda x: "啟用" if x == 1 else "停用", index=0 if int(current_row["is_active"]) == 1 else 1)
    if st.button("更新帳號狀態", use_container_width=True):
        try:
            update_user_status(int(user_id), int(target_status))
            st.success("帳號狀態更新成功。")
            st.rerun()
        except Exception as exc:
            st.error(f"更新失敗：{exc}")
