# 大豐物流部－支援系統（Streamlit Cloud 雲端資料庫版）

這一版改為 **Streamlit + PostgreSQL（雲端資料庫）**，可直接部署到 **Streamlit Community Cloud**。

## 特色
- Streamlit multipage
- 帳號登入與角色權限
- 企業入口首頁
- 支援需求 / 離組簽退 / 到組報到 / 主管總表
- PostgreSQL 雲端資料庫
- 支援 Streamlit secrets 設定

## 預設帳號
系統第一次連到空白資料庫時，會自動建立以下帳號：
- `admin / admin123`
- `supervisor / supervisor123`
- `staff01 / staff123`

## 本機測試
若你沒有先準備 PostgreSQL，系統會自動退回 SQLite 本機模式：
```bash
pip install -r requirements.txt
streamlit run app.py
```

## 正式部署到 Streamlit Community Cloud
### 1. 準備 GitHub Repo
把整個專案上傳到 GitHub。

### 2. 準備雲端 PostgreSQL
你可以使用：
- Supabase Postgres
- Neon Postgres
- Railway Postgres
- Render Postgres

你只要取得一條 PostgreSQL 連線字串即可。

範例：
```toml
[database]
url = "postgresql+psycopg2://USER:PASSWORD@HOST:5432/DBNAME"
```

### 3. 在 Streamlit Cloud 設定 Secrets
進入你的 App → Settings → Secrets，貼上：
```toml
[database]
url = "postgresql+psycopg2://USER:PASSWORD@HOST:5432/DBNAME"
```

### 4. 部署
Main file 設定為：
```text
app.py
```

## 重要說明
- 沒有設定 `st.secrets["database"]["url"]` 時，系統會退回本機 SQLite 模式
- 正式上線時建議一定要使用 PostgreSQL
- 若要更安全，請部署後立即修改預設帳號密碼

## 後續建議
- 增加密碼修改功能
- 增加操作日誌
- 串接 Email / LINE Notify
- 加入部門 / 使用者權限更細分控管
