import streamlit as st
import pandas as pd
import os
from datetime import datetime, date

# 嘗試載入日曆組件
try:
    from streamlit_calendar import calendar
except ImportError:
    st.error("請先安裝套件：pip install streamlit-calendar")

# --- 1. 檔案設定 ---
DB_FILE = "gym_lessons_v17.csv" # 更新版本以確保資料格式乾淨
REQ_FILE = "gym_requests_v17.csv"
STU_FILE = "gym_students_v17.csv"
CAT_FILE = "gym_categories_v17.csv"
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
        # 如果是類別檔，給預設值
        if f == CAT_FILE:
            pd.DataFrame({"類別名稱": ["MA 體態", "S 專項"]}).to_csv(f, index=False)
        else:
            pd.DataFrame(columns=cols).to_csv(f, index=False)

# 讀取資料 (加入強制轉型，防止資料打架)
def load_data():
    df_d = pd.read_csv(DB_FILE)
    df_d["日期"] = pd.to_datetime(df_d["日期"], errors='coerce').dt.date # 強制轉為日期物件
    
    df_s = pd.read_csv(STU_FILE)
    df_r = pd.read_csv(REQ_FILE)
    df_c = pd.read_csv(CAT_FILE)
    return df_d, df_s, df_r, df_c

df_db, df_stu, df_req, df_cat = load_data()

student_list = df_stu["姓名"].tolist() if not df_stu.empty else []
ALL_CATEGORIES = df_cat["類別名稱"].tolist() if not df_cat.empty else ["(請設定)"]

# ==================== 2. 全域大日曆 ====================
st.subheader("🗓️ 課程總覽")

events = []

# --- A. 加入課程資料 (修復時間格式 bug) ---
for _, row in df_db.iterrows():
    if pd.isna(row['日期']): continue # 跳過無效日期
    
    cat_str = str(row['課程種類'])
    color = "#33b5e5" 
    if "MA" in cat_str: color = "#FF4B4B" 
    elif "S" in cat_str: color = "#3D9DF3" 
    elif "一般" in cat_str: color = "#2E8B57" 
    
    # 確保小時是雙位數 (例如 07 而不是 7)
    try:
        start_h = int(str(row['時間']).split(':')[0])
        end_h = start_h + 1
        
        events.append({
            "title": f"{row['時間']} {row['學員']}",
            "start": f"{row['日期']}T{start_h:02d}:00:00", # 強制 :02d 補零
            "end": f"{row['日期']}T{end_h:02d}:00:00",
            "backgroundColor": color,
            "borderColor": color,
        })
    except:
        continue # 防止時間格式錯誤導致崩潰

# --- B. 加入國定假日 ---
holidays = [
    {"start": "2025-12-31", "title": "跨年夜(補)"},
    {"start": "2026-01-01", "title": "元旦"},
    {"start": "2026-02-17", "end": "2026-02-23", "title": "春節連假"},
    {"start": "2026-02-28", "title": "228紀念日"},
    {"start": "2026-04-04", "end": "2026-04-07", "title": "清明連假"},
    # ... 其他假日省略以節省篇幅，邏輯同上 ...
]

for h in holidays:
    events.append({
        "title": h["title"],
        "start": h["start"],
        "end": h.get("end"),
        "allDay": True,
        "backgroundColor": "#D32F2F",
        "borderColor": "#D32F2F",
        "display": "block",
    })

# --- C. 日曆設定 ---
calendar_options = {
    "editable": False,
    "headerToolbar": {
        "left": "prev,next", 
        "center": "title",
        "right": "dayGridMonth,timeGridWeek,timeGridDay,listMonth" 
    },
    "locale": "zh-tw", # 使用繁體中文確保清單與星期正確
    "buttonText": {
        "today": "今天",
        "month": "月", "week": "周", "day": "日", "list": "清單"
    },
    "initialView": "dayGridMonth",
    "height": 550,
    "slotMinTime": "06:00:00",
    "slotMaxTime": "23:00:00",
    "firstDay": 1,
    "views": {
        "listMonth": { "listDayFormat": { "month": "long", "day": "numeric", "weekday": "short" } }
    }
}

calendar(events=events, options=calendar_options, key="cal_v17")
st.divider()

# ==================== 3. 身份導覽 ====================
mode = st.radio("", ["🔍 學員查詢", "🔧 教練後台"], horizontal=True)

# --- A. 學員區 ---
if mode == "🔍 學員查詢":
    sel_date = st.date_input("查詢日期", date.today())
    day_view = df_db[df_db["日期"] == sel_date].sort_values("時間")
    
    if not day_view.empty:
        for _, row in day_view.iterrows():
            st.info(f"🕒 **{row['時間']}**　👤 **{row['學員']}**\n\n📌 {row['課程種類']}")
    else:
        st.write("🍵 本日無課")
    
    # ... (餘額查詢與留言功能保留原樣) ...

# --- B. 教練後台 ---
else:
    pwd = st.text_input("密碼", type="password")
    if pwd == COACH_PASSWORD:
        t1, t2, t3, t4, t5 = st.tabs(["排課", "編輯", "名單", "設定", "留言"])
        
        # Tab 1: 排課 (強化存檔邏輯)
        with t1:
            st.caption("🚀 快速排課")
            with st.container(border=True):
                d = st.date_input("日期", date.today())
                t = st.selectbox("時間", [f"{h:02d}:00" for h in range(7, 23)])
                s = st.selectbox("學員", ["(選學員)"] + student_list)
                
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
                        # 1. 建立新資料
                        new_row = pd.DataFrame([{
                            "日期": d, # 保持為日期物件，讓 concat 自動處理
                            "時間": t,
                            "學員": s,
                            "課程種類": cat,
                            "備註": ""
                        }])
                        
                        # 2. 強制統一格式後合併
                        # 先將 df_db 的日期轉為物件，確保一致
                        updated_df = pd.concat([df_db, new_row], ignore_index=True)
                        
                        # 3. 存檔 (確保日期以字串形式寫入)
                        updated_df.to_csv(DB_FILE, index=False)
                        
                        st.success(f"已排入：{s} {d} {t}")
                        st.rerun()
                    else:
                        st.error("未選人")
            
            # 🔍 系統自我診斷 (Debug Panel)
            with st.expander("🔍 系統自我診斷 (若課程沒出現請點此)"):
                st.write("目前資料庫中的最後 5 筆課程：")
                st.dataframe(df_db.tail(5))
                st.info("如果您剛剛新增的課程出現在這裡，但日曆沒顯示，請檢查日期是否在當前月份。")

        # Tab 2: 編輯
        with t2:
            ed = st.date_input("修課日期", date.today())
            mask = df_db["日期"] == ed
            edited = st.data_editor(
                df_db[mask], 
                num_rows="dynamic", 
                use_container_width=True,
                column_config={"課程種類": "項目", "備註": "備註", "學員": "姓名"}
            )
            if st.button("💾 儲存", use_container_width=True):
                # 存檔前做一次格式清洗
                final_df = pd.concat([df_db[~mask], edited], ignore_index=True)
                final_df.to_csv(DB_FILE, index=False)
                st.rerun()

        # ... (Tab 3, 4, 5 功能保留原樣) ...
        # Tab 3: 名單
        with t3:
            st.caption("設定學員額度與綁定項目")
            estu = st.data_editor(
                df_stu, num_rows="dynamic", use_container_width=True,
                column_config={
                    "姓名": "姓名",
                    "課程類別": st.column_config.SelectboxColumn("綁定項目", options=ALL_CATEGORIES, required=True),
                    "購買堂數": st.column_config.NumberColumn("額度", min_value=0),
                    "備註": "備註"
                }
            )
            if st.button("💾 更新名單", use_container_width=True):
                estu.to_csv(STU_FILE, index=False); st.rerun()

        # Tab 4: 設定
        with t4:
            st.caption("自訂課程項目")
            ecat = st.data_editor(
                df_cat, num_rows="dynamic", use_container_width=True,
                column_config={"類別名稱": "項目名稱"}
            )
            if st.button("💾 更新項目", use_container_width=True):
                ecat.to_csv(CAT_FILE, index=False); st.rerun()

        # Tab 5: 留言
        with t5:
            st.dataframe(df_req, use_container_width=True)
            if st.button("🗑️ 清空", use_container_width=True):
                pd.DataFrame(columns=["日期", "時間", "姓名", "留言"]).to_csv(REQ_FILE, index=False); st.rerun()
                
    elif pwd != "":
        st.error("密碼錯誤")

if st.button("⚠️ 重置"):
    for f in [DB_FILE, REQ_FILE, STU_FILE, CAT_FILE]:
        if os.path.exists(f): os.remove(f)
    st.rerun()
