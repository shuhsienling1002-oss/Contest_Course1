import streamlit as st
import pandas as pd
import os
from datetime import datetime, date

# 嘗試載入日曆組件
try:
    from streamlit_calendar import calendar
except ImportError:
    st.error("請在終端機執行 'pip install streamlit-calendar' 以啟用日曆！")

# --- 系統資料檔案路徑 ---
DB_FILE = "gym_lessons.csv"
REQ_FILE = "gym_requests.csv"
STU_FILE = "gym_students.csv"

st.set_page_config(page_title="林芸健身專業管理系統", layout="wide")

# 初始化：確保檔案存在
for f, cols in {
    DB_FILE: ["日期", "時間", "學員", "課程種類", "備註"],
    REQ_FILE: ["日期", "時間", "姓名", "留言"],
    STU_FILE: ["姓名", "剩餘堂數", "狀態"]
}.items():
    if not os.path.exists(f):
        pd.DataFrame(columns=cols).to_csv(f, index=False)

# ==================== 1. 資料讀取 ====================
st.sidebar.title("🧘‍♀️ 林芸專業管理")
mode = st.sidebar.radio("身份切換", ["🔍 學員查詢預約", "🔧 教練管理後台"])
sel_date = st.sidebar.date_input("📅 選擇操作日期", date.today())

df_db = pd.read_csv(DB_FILE)
df_db["日期"] = pd.to_datetime(df_db["日期"]).dt.date
df_stu = pd.read_csv(STU_FILE)
df_req = pd.read_csv(REQ_FILE)
student_options = df_stu["姓名"].tolist() if not df_stu.empty else ["(請先在後台新增學員)"]

# --- A. 學員查詢預約 ---
if mode == "🔍 學員查詢預約":
    st.header(f"📅 {sel_date} 課程查詢")
    day_view = df_db[df_db["日期"] == sel_date]
    c1, gap, c2 = st.columns([2, 0.1, 1])
    with c1:
        if not day_view.empty:
            st.dataframe(day_view[["時間", "學員", "課程種類"]].sort_values("時間"), hide_index=True, use_container_width=True)
        else: st.info("本日目前無排定課程。")
    with c2:
        st.subheader("💡 堂數查詢")
        if not df_stu.empty:
            s_name = st.selectbox("請選擇姓名", student_options, key="stu_q")
            s_info = df_stu[df_stu["姓名"] == s_name].iloc[0]
            st.metric("剩餘堂數", f"{int(float(s_info['剩餘堂數']))} 堂")
        st.divider()
        st.subheader("📝 登記預約留言")
        with st.form("stu_req", clear_on_submit=True):
            un, ut, um = st.text_input("姓名"), st.selectbox("時段", [f"{h:02d}:00" for h in range(7, 23)]), st.text_area("留言")
            if st.form_submit_button("送出"):
                pd.concat([df_req, pd.DataFrame([{"日期":str(sel_date),"時間":ut,"姓名":un,"留言":um}])]).to_csv(REQ_FILE, index=False)
                st.success("已留言！")

# --- B. 教練管理後台 ---
else:
    st.header("🔧 教練專業管理後台")
    t_cal, t1, t2, t3, t4 = st.tabs(["📊 全域大日曆", "✨ 線上排課", "📋 編輯課表", "👤 學員管理", "✉️ 預約清單"])
    
    with t_cal:
        st.subheader("🗓️ 全月課程總覽")
        events = []
        for _, row in df_db.iterrows():
            color = "#FF4B4B" if "MA" in str(row['課程種類']) else "#3D9DF3"
            events.append({"title": f"{row['時間']} {row['學員']}", "start": f"{row['日期']}T{row['時間']}:00", "backgroundColor": color})
        calendar(events=events, options={"initialView": "dayGridMonth", "headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth,timeGridWeek"}}, key="coach_cal")

    with t1:
        with st.form("add_f", clear_on_submit=True):
            ca, cb, cc, cd = st.columns(4)
            d, t = ca.date_input("日期", sel_date), cb.selectbox("時間", [f"{h:02d}:00" for h in range(7, 23)])
            s, cat = cc.selectbox("學員", student_options), cd.selectbox("類別", ["MA 體態", "S 專項", "一般訓練"])
            if st.form_submit_button("➕ 新增課程"):
                if s != "(請先在後台新增學員)":
                    new_l = pd.DataFrame([{"日期":str(d),"時間":t,"學員":s,"課程種類":cat,"備註":""}])
                    pd.concat([df_db, new_l]).to_csv(DB_FILE, index=False); st.success(f"已排入課程：{s}"); st.rerun()

    with t2:
        day_edit = df_db[df_db["日期"] == sel_date]
        edited = st.data_editor(day_edit, num_rows="dynamic", use_container_width=True)
        if st.button("💾 儲存修改"):
            df_db = pd.concat([df_db[df_db["日期"] != sel_date], edited]).to_csv(DB_FILE, index=False); st.rerun()

    with t3:
        st.subheader("👤 學員名單管理")
        new_stu_df = st.data_editor(df_stu, num_rows="dynamic", use_container_width=True)
        if st.button("💾 儲存名單"):
            new_stu_df.to_csv(STU_FILE, index=False); st.success("名單已更新！"); st.rerun()

    with t4:
        st.dataframe(df_req, use_container_width=True)
        if st.button("🗑️ 清空留言"):
            pd.DataFrame(columns=["日期", "時間", "姓名", "留言"]).to_csv(REQ_FILE, index=False); st.rerun()

if st.sidebar.button("⚠️ 系統重置"):
    for f in [DB_FILE, REQ_FILE, STU_FILE]: os.remove(f); st.rerun()