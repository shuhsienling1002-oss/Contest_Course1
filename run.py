import streamlit as st
import pandas as pd
import os
from datetime import datetime, date

# 嘗試載入日曆組件
try:
    from streamlit_calendar import calendar
except ImportError:
    st.error("請在終端機執行 'pip install streamlit-calendar' 以啟用日曆！")

# --- 1. 系統安全性與檔案設定 ---
DB_FILE = "gym_lessons_v7.csv"
REQ_FILE = "gym_req_v7.csv"
STU_FILE = "gym_students_v7.csv"
COACH_PASSWORD = "1234"  # 👈 預設密碼已更新為 1234

st.set_page_config(page_title="林芸健身專業管理系統", layout="wide")

# 初始化檔案
for f, cols in {
    DB_FILE: ["日期", "時間", "學員", "課程種類", "備註"],
    REQ_FILE: ["日期", "時間", "姓名", "留言"],
    STU_FILE: ["姓名", "剩餘堂數", "狀態"]
}.items():
    if not os.path.exists(f):
        pd.DataFrame(columns=cols).to_csv(f, index=False)

# 讀取資料
df_db = pd.read_csv(DB_FILE)
df_db["日期"] = pd.to_datetime(df_db["日期"]).dt.date
df_stu = pd.read_csv(STU_FILE)
df_req = pd.read_csv(REQ_FILE)
student_options = df_stu["姓名"].tolist() if not df_stu.empty else ["(請先在後台新增學員)"]

# ==================== 2. 全域大日曆 (所有人皆可見) ====================
st.header("🗓️ 林芸健身課程全月總覽")
st.info("💡 藍色標記為一般課程，紅色標記為 MA 體態課程。")

events = []
for _, row in df_db.iterrows():
    color = "#FF4B4B" if "MA" in str(row['課程種類']) else "#3D9DF3"
    events.append({
        "title": f"{row['時間']} {row['學員']}",
        "start": f"{row['日期']}T{row['時間']}:00",
        "backgroundColor": color,
        "borderColor": color,
    })

# 顯示唯讀日曆
calendar(events=events, options={"initialView": "dayGridMonth", "editable": False}, key="global_calendar")

st.divider()

# ==================== 3. 身份導覽與權限控制 ====================
st.sidebar.title("🧘‍♀️ 林芸專業管理")
mode = st.sidebar.radio("請選擇身份模式", ["🔍 學員專區 (查詢/預約)", "🔧 教練管理 (密碼登入)"])

# --- A. 學員專區 ---
if mode == "🔍 學員專區 (查詢/預約)":
    st.subheader("📋 查詢特定日期課表")
    sel_date = st.date_input("選擇日期", date.today())
    day_view = df_db[df_db["日期"] == sel_date]
    
    c1, gap, c2 = st.columns([2, 0.1, 1])
    with c1:
        if not day_view.empty:
            st.dataframe(day_view[["時間", "學員", "課程種類"]].sort_values("時間"), hide_index=True, use_container_width=True)
        else: st.warning("本日目前無排定課程。")
    with c2:
        st.subheader("💡 堂數查詢")
        if not df_stu.empty:
            s_name = st.selectbox("您的姓名", student_options)
            s_info = df_stu[df_stu["姓名"] == s_name].iloc[0]
            st.metric("剩餘堂數", f"{int(float(s_info['剩餘堂數']))} 堂")
        st.divider()
        st.subheader("📝 登記留言預約")
        with st.form("stu_req", clear_on_submit=True):
            un, ut, um = st.text_input("姓名"), st.selectbox("時段", [f"{h:02d}:00" for h in range(7, 23)]), st.text_area("留言內容")
            if st.form_submit_button("確認送出"):
                pd.concat([df_req, pd.DataFrame([{"日期":str(sel_date),"時間":ut,"姓名":un,"留言":um}])]).to_csv(REQ_FILE, index=False)
                st.success("已留言！教練會主動與您聯繫。")

# --- B. 教練管理 (密碼驗證) ---
else:
    st.sidebar.divider()
    pwd = st.sidebar.text_input("🔑 請輸入登入密碼", type="password")
    
    if pwd == COACH_PASSWORD:
        st.sidebar.success("✅ 教練已登入")
        st.header("🔧 教練專業管理後台")
        t1, t2, t3, t4 = st.tabs(["✨ 線上快速排課", "📋 編輯/刪除課表", "👤 學員名單維護", "✉️ 預約留言單"])
        
        with t1:
            with st.form("add_f", clear_on_submit=True):
                ca, cb, cc, cd = st.columns(4)
                d, t = ca.date_input("日期", date.today()), cb.selectbox("時間", [f"{h:02d}:00" for h in range(7, 23)])
                s, cat = cc.selectbox("學員", student_options), cd.selectbox("類別", ["MA 體態", "S 專項", "一般訓練"])
                if st.form_submit_button("➕ 點擊排入課表"):
                    if s != "(請先在後台新增學員)":
                        new_l = pd.DataFrame([{"日期":str(d),"時間":t,"學員":s,"課程種類":cat,"備註":""}])
                        pd.concat([df_db, new_l]).to_csv(DB_FILE, index=False); st.success(f"已排入課程：{s}"); st.rerun()

        with t2:
            edit_date = st.date_input("選取欲修改日期", date.today())
            day_edit = df_db[df_db["日期"] == edit_date]
            edited = st.data_editor(day_edit, num_rows="dynamic", use_container_width=True)
            if st.button("💾 儲存修改"):
                df_db = pd.concat([df_db[df_db["日期"] != edit_date], edited]).to_csv(DB_FILE, index=False); st.success("已存檔！"); st.rerun()

        with t3:
            st.subheader("👤 學員名單維護")
            new_stu_df = st.data_editor(df_stu, num_rows="dynamic", use_container_width=True)
            if st.button("💾 儲存學員資料"):
                new_stu_df.to_csv(STU_FILE, index=False); st.success("名單更新完成！"); st.rerun()

        with t4:
            st.dataframe(df_req, use_container_width=True)
            if st.button("🗑️ 清空留言紀錄"):
                pd.DataFrame(columns=["日期", "時間", "姓名", "留言"]).to_csv(REQ_FILE, index=False); st.rerun()
    elif pwd != "":
        st.sidebar.error("❌ 密碼錯誤")
