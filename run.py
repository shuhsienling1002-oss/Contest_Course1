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
DB_FILE = "gym_lessons_v12.csv"
REQ_FILE = "gym_requests_v12.csv"
STU_FILE = "gym_students_v12.csv"
CAT_FILE = "gym_categories_v12.csv"
COACH_PASSWORD = "1234"

st.set_page_config(page_title="林芸健身", layout="wide", initial_sidebar_state="collapsed")

# 初始化檔案
if not os.path.exists(STU_FILE):
    pd.DataFrame(columns=["姓名", "購買堂數", "課程類別", "備註"]).to_csv(STU_FILE, index=False)
if not os.path.exists(DB_FILE):
    pd.DataFrame(columns=["日期", "時間", "學員", "課程種類", "備註"]).to_csv(DB_FILE, index=False)
if not os.path.exists(REQ_FILE):
    pd.DataFrame(columns=["日期", "時間", "姓名", "留言"]).to_csv(REQ_FILE, index=False)
if not os.path.exists(CAT_FILE):
    pd.DataFrame({"類別名稱": ["MA 體態", "S 專項"]}).to_csv(CAT_FILE, index=False)

# 讀取資料
df_db = pd.read_csv(DB_FILE)
df_db["日期"] = pd.to_datetime(df_db["日期"]).dt.date
df_stu = pd.read_csv(STU_FILE)
df_req = pd.read_csv(REQ_FILE)
df_cat = pd.read_csv(CAT_FILE)

student_list = df_stu["姓名"].tolist() if not df_stu.empty else []
ALL_CATEGORIES = df_cat["類別名稱"].tolist() if not df_cat.empty else ["(請設定)"]

# ==================== 2. 全域大日曆 (強制顯示) ====================
st.subheader("🗓️ 課程總覽") # 標題簡單化

events = []
for _, row in df_db.iterrows():
    cat_str = str(row['課程種類'])
    color = "#FF4B4B" if "MA" in cat_str else ("#3D9DF3" if "S" in cat_str else "#2E8B57")
    events.append({
        "title": f"{row['時間']} {row['學員']}", # 日曆上只顯示 時間+人名 (手機看才不會擠)
        "start": f"{row['日期']}T{row['時間']}:00",
        "end": f"{row['日期']}T{int(row['時間'][:2])+1}:00:00",
        "backgroundColor": color,
        "borderColor": color,
    })

calendar_options = {
    "editable": False,
    "headerToolbar": {
        "left": "prev,next", # 手機版把 today 拿掉省空間
        "center": "title",
        "right": "dayGridMonth,listMonth" # 手機只留 月曆 跟 清單 兩種最實用
    },
    "buttonText": {"month": "月曆", "list": "清單"},
    "initialView": "dayGridMonth", # 預設回月曆，確保您看得到
    "height": 450,
    "locale": "zh-tw",
}
# 這裡直接渲染日曆，不包在任何 Tab 裡，確保不會「不見」
calendar(events=events, options=calendar_options, key="mobile_cal")
st.divider()

# ==================== 3. 身份導覽 ====================
mode = st.radio("", ["🔍 學員查詢", "🔧 教練後台"], horizontal=True) # 改成橫向按鈕，省空間

# --- A. 學員區 (極簡化) ---
if mode == "🔍 學員查詢":
    sel_date = st.date_input("查詢日期", date.today())
    day_view = df_db[df_db["日期"] == sel_date].sort_values("時間")
    
    # 手機極簡顯示：不用表格，改用條列
    if not day_view.empty:
        for _, row in day_view.iterrows():
            # 使用 info 框框顯示，字大清晰
            st.info(f"🕒 **{row['時間']}**　👤 **{row['學員']}**\n\n📌 {row['課程種類']}")
    else:
        st.write("🍵 本日無課")

    st.divider()
    
    # 堂數查詢
    if student_list:
        s_name = st.selectbox("查詢餘額 (選擇姓名)", student_list)
        s_data = df_stu[df_stu["姓名"] == s_name].iloc[0]
        used = len(df_db[df_db["學員"] == s_name])
        total = int(float(s_data['購買堂數'])) if pd.notnull(s_data['購買堂數']) else 0
        left = total - used
        
        # 極簡數據
        c1, c2, c3 = st.columns(3)
        c1.metric("總額", total)
        c2.metric("已上", used)
        c3.metric("餘額", left, delta_color="normal")
        
    with st.expander("📝 預約/留言"):
        with st.form("req"):
            un = st.text_input("姓名", value=s_name if student_list else "")
            ut = st.selectbox("時段", [f"{h:02d}:00" for h in range(7, 23)])
            um = st.text_area("備註") # 簡化文字
            if st.form_submit_button("送出", use_container_width=True):
                pd.concat([df_req, pd.DataFrame([{"日期":str(sel_date),"時間":ut,"姓名":un,"留言":um}])]).to_csv(REQ_FILE, index=False)
                st.success("已送出")

# --- B. 教練後台 ---
else:
    pwd = st.text_input("密碼", type="password")
    if pwd == COACH_PASSWORD:
        t1, t2, t3, t4, t5 = st.tabs(["排課", "編輯", "名單", "設定", "留言"])
        
        # --- Tab 1: 排課 (極簡輸入) ---
        with t1:
            st.caption("🚀 快速排課")
            with st.container(border=True):
                d = st.date_input("日期", date.today())
                t = st.selectbox("時間", [f"{h:02d}:00" for h in range(7, 23)])
                s = st.selectbox("學員", ["(選學員)"] + student_list)
                
                # 自動鎖定邏輯
                opts = ALL_CATEGORIES
                if s != "(選學員)":
                    rec = df_stu[df_stu["姓名"] == s]
                    if not rec.empty:
                        saved = rec.iloc[0]["課程類別"]
                        if saved and saved in ALL_CATEGORIES:
                            opts = [saved] # 鎖定
                
                cat = st.selectbox("項目", opts)
                
                if st.button("➕ 新增", type="primary", use_container_width=True):
                    if s != "(選學員)":
                        new = pd.DataFrame([{"日期":str(d), "時間":t, "學員":s, "課程種類":cat, "備註":""}])
                        pd.concat([df_db, new]).to_csv(DB_FILE, index=False)
                        st.success(f"已排：{s}")
                        st.rerun()
                    else:
                        st.error("未選人")

        # --- Tab 2: 編輯 (表格文字簡化) ---
        with t2:
            ed = st.date_input("修課日期", date.today())
            mask = df_db["日期"] == ed
            # 使用 column_config 把標頭改短，但不改動資料庫欄位
            edited = st.data_editor(
                df_db[mask], 
                num_rows="dynamic", 
                use_container_width=True,
                column_config={
                    "課程種類": "項目",
                    "備註": "備註",
                    "學員": "姓名"
                }
            )
            if st.button("💾 儲存", use_container_width=True):
                pd.concat([df_db[~mask], edited]).to_csv(DB_FILE, index=False)
                st.rerun()

        # --- Tab 3: 名單 (表格文字簡化) ---
        with t3:
            st.caption("設定學員額度與綁定項目")
            estu = st.data_editor(
                df_stu,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "姓名": "姓名",
                    "課程類別": st.column_config.SelectboxColumn("綁定項目", options=ALL_CATEGORIES, required=True),
                    "購買堂數": st.column_config.NumberColumn("額度", min_value=0),
                    "備註": "備註"
                }
            )
            if st.button("💾 更新名單", use_container_width=True):
                estu.to_csv(STU_FILE, index=False)
                st.rerun()

        # --- Tab 4: 設定 ---
        with t4:
            st.caption("自訂課程項目")
            ecat = st.data_editor(
                df_cat, 
                num_rows="dynamic", 
                use_container_width=True,
                column_config={"類別名稱": "項目名稱"}
            )
            if st.button("💾 更新項目", use_container_width=True):
                ecat.to_csv(CAT_FILE, index=False)
                st.rerun()

        with t5:
            st.dataframe(df_req, use_container_width=True)
            if st.button("🗑️ 清空", use_container_width=True):
                pd.DataFrame(columns=["日期", "時間", "姓名", "留言"]).to_csv(REQ_FILE, index=False)
                st.rerun()
                
    elif pwd != "":
        st.error("密碼錯誤")

if st.button("⚠️ 重置"):
    for f in [DB_FILE, REQ_FILE, STU_FILE, CAT_FILE]:
        if os.path.exists(f): os.remove(f)
    st.rerun()
