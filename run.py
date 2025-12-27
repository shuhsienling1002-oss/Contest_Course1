import streamlit as st
import pandas as pd
import os
from datetime import datetime, date

# 嘗試載入日曆組件
try:
    from streamlit_calendar import calendar
except ImportError:
    st.error("請先安裝套件：pip install streamlit-calendar")

# --- 1. 檔案設定 (維持不變) ---
DB_FILE = "gym_lessons_v19.csv"
REQ_FILE = "gym_requests_v19.csv"
STU_FILE = "gym_students_v19.csv"
CAT_FILE = "gym_categories_v19.csv"
COACH_PASSWORD = "1234"

st.set_page_config(page_title="林芸健身", layout="wide", initial_sidebar_state="collapsed")

# 初始化檔案
for f, cols in {
    DB_FILE: ["日期", "時間", "學員", "課程種類", "備註"],
    REQ_FILE: ["日期", "時間", "姓名", "留言"],
    STU_FILE: ["姓名", "購買堂數", "課程類別", "備註"],
    CAT_FILE: ["類別名稱"]
}.items():
    if not os.path.exists(f):
        if f == CAT_FILE:
            pd.DataFrame({"類別名稱": ["MA 體態", "S 專項"]}).to_csv(f, index=False)
        else:
            pd.DataFrame(columns=cols).to_csv(f, index=False)

# 讀取資料
def load_data():
    df_d = pd.read_csv(DB_FILE)
    df_d["日期"] = pd.to_datetime(df_d["日期"], errors='coerce').dt.date
    df_s = pd.read_csv(STU_FILE)
    df_r = pd.read_csv(REQ_FILE)
    df_c = pd.read_csv(CAT_FILE)
    return df_d, df_s, df_r, df_c

df_db, df_stu, df_req, df_cat = load_data()

student_list = df_stu["姓名"].tolist() if not df_stu.empty else []
ALL_CATEGORIES = df_cat["類別名稱"].tolist() if not df_cat.empty else ["(請設定)"]

# ==================== 2. 全域大日曆 (視覺優化：白底彩字) ====================
st.subheader("🗓️ 課程總覽")

events = []

# --- A. 加入課程資料 ---
for _, row in df_db.iterrows():
    if pd.isna(row['日期']): continue
    
    cat_str = str(row['課程種類'])
    
    # 設定顏色邏輯：這次是設定「字體顏色 (textColor)」
    if "MA" in cat_str: 
        theme_color = "#D32F2F" # 紅色
    elif "S" in cat_str: 
        theme_color = "#1976D2" # 藍色
    elif "一般" in cat_str: 
        theme_color = "#388E3C" # 綠色
    else:
        theme_color = "#555555" # 其他灰黑
    
    try:
        start_h = int(str(row['時間']).split(':')[0])
        end_h = start_h + 1
        events.append({
            # 修正：標題只放名字，避免重複顯示時間
            "title": f"{row['學員']}", 
            "start": f"{row['日期']}T{start_h:02d}:00:00",
            "end": f"{row['日期']}T{end_h:02d}:00:00",
            
            # 視覺設定：背景白，字體彩色，邊框彩色
            "backgroundColor": "#FFFFFF", 
            "textColor": theme_color,     
            "borderColor": theme_color,
        })
    except: continue

# --- B. 加入國定假日 (維持紅底白字) ---
holidays = [
    {"start": "2025-12-31", "title": "跨年夜(補)"},
    {"start": "2026-01-01", "title": "元旦"},
    {"start": "2026-02-17", "end": "2026-02-23", "title": "春節連假"},
    {"start": "2026-02-28", "title": "228紀念日"},
    {"start": "2026-04-04", "end": "2026-04-07", "title": "清明連假"},
    {"start": "2025-01-01", "title": "元旦"},
    {"start": "2025-01-25", "end": "2025-02-03", "title": "春節"},
]

for h in holidays:
    events.append({
        "title": h["title"],
        "start": h["start"],
        "end": h.get("end"),
        "allDay": True,
        "backgroundColor": "#D32F2F", # 假日維持顯眼的全紅
        "borderColor": "#D32F2F",
        "textColor": "#FFFFFF",
        "display": "block",
    })

# --- C. 日曆設定 (保留所有設定) ---
calendar_options = {
    "editable": False,
    "headerToolbar": {
        "left": "prev,next", 
        "center": "title",
        "right": "dayGridMonth,timeGridWeek,timeGridDay,listMonth" 
    },
    "locale": "en", # 維持英文核心（確保無「日」字）
    "buttonText": {
        "today": "今天", "month": "月", "week": "周", "day": "日", "list": "清單"
    },
    "dayHeaderFormat": { "weekday": "short" }, # 標題只顯示 Mon, Tue
    "initialView": "dayGridMonth",
    "height": 550,
    "slotMinTime": "06:00:00",
    "slotMaxTime": "23:00:00",
    "firstDay": 1,
    
    # 時間格式優化：顯示 11:00 而不是 11a
    "eventTimeFormat": {
        "hour": "2-digit",
        "minute": "2-digit",
        "hour12": False
    },
    
    "views": {
        "listMonth": {
            "listDayFormat": { "month": "numeric", "day": "numeric", "weekday": "short" }
        }
    }
}

calendar(events=events, options=calendar_options, key="cal_v19_final")
st.divider()

# ==================== 3. 身份導覽 (保留完整功能) ====================
mode = st.radio("", ["🔍 學員查詢", "🔧 教練後台"], horizontal=True)

# --- A. 學員區 ---
if mode == "🔍 學員查詢":
    sel_date = st.date_input("查詢日期", date.today())
    day_view = df_db[df_db["日期"] == sel_date].sort_values("時間")
    
    if not day_view.empty:
        for _, row in day_view.iterrows():
            # 這裡也同步一下顏色邏輯 (用 emoji 區分)
            icon = "🔴" if "MA" in str(row['課程種類']) else ("🔵" if "S" in str(row['課程種類']) else "🟢")
            st.info(f"{icon} **{row['時間']}**　👤 **{row['學員']}**\n\n📌 {row['課程種類']}")
    else:
        st.write("🍵 本日無課")
    
    st.divider()
    if student_list:
        s_name = st.selectbox("查詢餘額 (選擇姓名)", student_list)
        s_data = df_stu[df_stu["姓名"] == s_name].iloc[0]
        used = len(df_db[df_db["學員"] == s_name])
        total = int(float(s_data['購買堂數'])) if pd.notnull(s_data['購買堂數']) else 0
        left = total - used
        
        c1, c2, c3 = st.columns(3)
        c1.metric("總額", total); c2.metric("已上", used); c3.metric("餘額", left)
        
    with st.expander("📝 預約/留言"):
        with st.form("req"):
            un = st.text_input("姓名", value=s_name if student_list else "")
            ut = st.selectbox("時段", [f"{h:02d}:00" for h in range(7, 23)])
            um = st.text_area("備註")
            if st.form_submit_button("送出", use_container_width=True):
                pd.concat([df_req, pd.DataFrame([{"日期":str(sel_date),"時間":ut,"姓名":un,"留言":um}])]).to_csv(REQ_FILE, index=False)
                st.success("已送出")

# --- B. 教練後台 ---
else:
    pwd = st.text_input("密碼", type="password")
    if pwd == COACH_PASSWORD:
        t1, t2, t3, t4, t5 = st.tabs(["排課", "編輯", "名單", "設定", "留言"])
        
        with t1:
            st.caption("🚀 快速排課")
            with st.container(border=True):
                d = st.date_input("日期", date.today())
                t = st.selectbox("時間", [f"{h:02d}:00" for h in range(7, 23)])
                s = st.selectbox("學員", ["(選學員)"] + student_list)
                
                # 保留防呆鎖定邏輯
                opts = ALL_CATEGORIES
                if s != "(選學員)":
                    rec = df_stu[df_stu["姓名"] == s]
                    if not rec.empty:
                        saved = rec.iloc[0]["課程類別"]
                        if saved and saved in ALL_CATEGORIES:
                            opts = [saved]
                
                cat = st.selectbox("項目", opts)
                
                if st.button("➕ 新增", type="primary", use_container_width=True):
                    if s != "(選學員)":
                        new_row = pd.DataFrame([{"日期": d, "時間": t, "學員": s, "課程種類": cat, "備註": ""}])
                        updated_df = pd.concat([df_db, new_row], ignore_index=True)
                        updated_df.to_csv(DB_FILE, index=False)
                        st.success(f"已排：{s}"); st.rerun()
                    else: st.error("未選人")

        with t2:
            ed = st.date_input("修課日期", date.today())
            mask = df_db["日期"] == ed
            edited = st.data_editor(df_db[mask], num_rows="dynamic", use_container_width=True, column_config={"課程種類":"項目", "備註":"備註", "學員":"姓名"})
            if st.button("💾 儲存", use_container_width=True):
                pd.concat([df_db[~mask], edited], ignore_index=True).to_csv(DB_FILE, index=False); st.rerun()

        with t3:
            st.caption("設定學員額度與綁定項目")
            estu = st.data_editor(df_stu, num_rows="dynamic", use_container_width=True, column_config={"姓名":"姓名", "課程類別":st.column_config.SelectboxColumn("綁定項目", options=ALL_CATEGORIES), "購買堂數":st.column_config.NumberColumn("額度")})
            if st.button("💾 更新名單", use_container_width=True):
                estu.to_csv(STU_FILE, index=False); st.rerun()

        with t4:
            st.caption("自訂課程項目")
            ecat = st.data_editor(df_cat, num_rows="dynamic", use_container_width=True, column_config={"類別名稱":"項目名稱"})
            if st.button("💾 更新項目", use_container_width=True):
                ecat.to_csv(CAT_FILE, index=False); st.rerun()

        with t5:
            st.dataframe(df_req, use_container_width=True)
            if st.button("🗑️ 清空", use_container_width=True):
                pd.DataFrame(columns=["日期", "時間", "姓名", "留言"]).to_csv(REQ_FILE, index=False); st.rerun()
                
    elif pwd != "": st.error("密碼錯誤")

if st.button("⚠️ 重置"):
    for f in [DB_FILE, REQ_FILE, STU_FILE, CAT_FILE]:
        if os.path.exists(f): os.remove(f)
    st.rerun()
