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
# 更新版本號，確保檔案結構更新
DB_FILE = "gym_lessons_v10.csv"
REQ_FILE = "gym_requests_v10.csv"
STU_FILE = "gym_students_v10.csv"
CAT_FILE = "gym_categories_v10.csv" # 新增：專門存儲您自訂的課程類別
COACH_PASSWORD = "1234"

st.set_page_config(page_title="林芸健身專業管理系統", layout="wide")

# 初始化檔案
if not os.path.exists(STU_FILE):
    pd.DataFrame(columns=["姓名", "購買堂數", "課程類別", "備註"]).to_csv(STU_FILE, index=False)
if not os.path.exists(DB_FILE):
    pd.DataFrame(columns=["日期", "時間", "學員", "課程種類", "備註"]).to_csv(DB_FILE, index=False)
if not os.path.exists(REQ_FILE):
    pd.DataFrame(columns=["日期", "時間", "姓名", "留言"]).to_csv(REQ_FILE, index=False)
# 初始化課程類別檔 (若不存在，給一個預設值以免空白，之後您可刪除)
if not os.path.exists(CAT_FILE):
    pd.DataFrame({"類別名稱": ["MA 體態管理", "S 專項訓練"]}).to_csv(CAT_FILE, index=False)

# 讀取資料
df_db = pd.read_csv(DB_FILE)
df_db["日期"] = pd.to_datetime(df_db["日期"]).dt.date
df_stu = pd.read_csv(STU_FILE)
df_req = pd.read_csv(REQ_FILE)
df_cat = pd.read_csv(CAT_FILE)

# 準備下拉選單資料
student_list = df_stu["姓名"].tolist() if not df_stu.empty else []
# 讀取您自訂的課程類別
COURSE_CATEGORIES = df_cat["類別名稱"].tolist() if not df_cat.empty else ["(請先設定課程)"]

# ==================== 2. 全域大日曆 (月/周/日 視圖) ====================
st.header("🗓️ 林芸健身課程總覽")

events = []
for _, row in df_db.iterrows():
    # 簡單的變色邏輯：MA=紅, S=藍, 其他=綠
    cat_str = str(row['課程種類'])
    if "MA" in cat_str: color = "#FF4B4B"
    elif "S" in cat_str: color = "#3D9DF3"
    else: color = "#2E8B57" # 其他自訂課程用綠色
    
    events.append({
        "title": f"{row['學員']} ({row['課程種類']})", 
        "start": f"{row['日期']}T{row['時間']}:00",
        "end": f"{row['日期']}T{int(row['時間'][:2])+1}:00:00",
        "backgroundColor": color,
        "borderColor": color,
    })

calendar_options = {
    "editable": False,
    "headerToolbar": {
        "left": "prev,next today",
        "center": "title",
        "right": "dayGridMonth,timeGridWeek,timeGridDay"
    },
    "buttonText": {"today": "今天", "month": "月", "week": "周", "day": "日"},
    "initialView": "dayGridMonth",
    "slotMinTime": "06:00:00",
    "slotMaxTime": "23:00:00",
    "locale": "zh-tw",
}
calendar(events=events, options=calendar_options, key="global_cal")
st.divider()

# ==================== 3. 身份導覽 ====================
st.sidebar.title("🧘‍♀️ 林芸專業管理")
mode = st.sidebar.radio("身份切換", ["🔍 學員專區", "🔧 教練後台"])

# --- A. 學員專區 ---
if mode == "🔍 學員專區":
    st.subheader("📋 課表查詢")
    sel_date = st.date_input("選擇日期", date.today())
    day_view = df_db[df_db["日期"] == sel_date]
    
    c1, c2 = st.columns([2, 1])
    with c1:
        if not day_view.empty:
            st.dataframe(day_view[["時間", "學員", "課程種類"]], hide_index=True, use_container_width=True)
        else: st.info("本日無課程。")
    with c2:
        st.subheader("💡 查詢我的堂數")
        if student_list:
            s_name = st.selectbox("您的姓名", student_list)
            # 計算邏輯：購買堂數 - 已上課堂數
            s_data = df_stu[df_stu["姓名"] == s_name].iloc[0]
            used_count = len(df_db[df_db["學員"] == s_name])
            purchased = int(float(s_data['購買堂數'])) if pd.notnull(s_data['購買堂數']) and s_data['購買堂數'] != "" else 0
            remaining = purchased - used_count
            
            st.metric("購買總堂數", f"{purchased} 堂")
            st.metric("目前剩餘", f"{remaining} 堂", delta=f"- 已上 {used_count} 堂", delta_color="inverse")
            st.caption(f"預設類別：{s_data['課程類別']}")
            
        st.divider()
        with st.form("req"):
            st.write("📝 **預約留言**")
            un = st.text_input("姓名", value=s_name if student_list else "")
            ut = st.selectbox("時段", [f"{h:02d}:00" for h in range(7, 23)])
            um = st.text_area("內容")
            if st.form_submit_button("送出"):
                pd.concat([df_req, pd.DataFrame([{"日期":str(sel_date),"時間":ut,"姓名":un,"留言":um}])]).to_csv(REQ_FILE, index=False)
                st.success("已留言！")

# --- B. 教練後台 ---
else:
    pwd = st.sidebar.text_input("🔑 教練密碼", type="password")
    if pwd == COACH_PASSWORD:
        st.sidebar.success("已登入")
        # 新增第 4 個 Tab: ⚙️ 課程類別設定
        t1, t2, t3, t4, t5 = st.tabs(["✨ 智能排課", "📋 編輯課表", "👤 學員名單", "⚙️ 自訂課程類別", "✉️ 留言板"])
        
        # --- Tab 1: 智能排課 (連動您自訂的課程) ---
        with t1:
            st.subheader("🚀 快速排課 (自動帶入類別)")
            
            c1, c2, c3, c4 = st.columns(4)
            d = c1.date_input("日期", date.today())
            t = c2.selectbox("時間", [f"{h:02d}:00" for h in range(7, 23)])
            
            # 1. 選擇學員
            s_select = c3.selectbox("選擇學員", ["(請選擇)"] + student_list)
            
            # 2. 自動判斷該學員的預設類別 (從您自訂的清單中找)
            default_cat_index = 0
            if s_select != "(請選擇)":
                stu_record = df_stu[df_stu["姓名"] == s_select]
                if not stu_record.empty:
                    saved_cat = stu_record.iloc[0]["課程類別"]
                    if saved_cat in COURSE_CATEGORIES:
                        default_cat_index = COURSE_CATEGORIES.index(saved_cat)
            
            # 3. 類別選單 (內容來自 Tab 4 的設定)
            cat_select = c4.selectbox("課程類別", COURSE_CATEGORIES, index=default_cat_index)
            
            if st.button("➕ 確認新增課程", type="primary"):
                if s_select != "(請選擇)":
                    new_row = pd.DataFrame([{"日期":str(d), "時間":t, "學員":s_select, "課程種類":cat_select, "備註":""}])
                    pd.concat([df_db, new_row]).to_csv(DB_FILE, index=False)
                    st.success(f"✅ 已新增：{s_select} - {cat_select}")
                    st.rerun()
                else:
                    st.error("請先選擇學員！")

        # --- Tab 2: 編輯課表 ---
        with t2:
            edit_d = st.date_input("選擇修改日期", date.today())
            mask = df_db["日期"] == edit_d
            edited = st.data_editor(df_db[mask], num_rows="dynamic", use_container_width=True, key="editor")
            if st.button("💾 儲存變更"):
                pd.concat([df_db[~mask], edited]).to_csv(DB_FILE, index=False)
                st.success("更新成功！"); st.rerun()

        # --- Tab 3: 學員名單維護 (連動自訂課程) ---
        with t3:
            st.subheader("👤 設定學員購買堂數與類別")
            st.info("在此設定學員的預設類別（選單內容來自「⚙️ 自訂課程類別」）。")
            
            edited_stu = st.data_editor(
                df_stu,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "課程類別": st.column_config.SelectboxColumn(
                        "課程類別 (預設)",
                        width="medium",
                        options=COURSE_CATEGORIES, # 這裡會自動更新為您自訂的課程
                        required=True
                    ),
                    "購買堂數": st.column_config.NumberColumn("購買堂數", min_value=0, step=1)
                }
            )
            
            if st.button("💾 儲存名單設定"):
                edited_stu.to_csv(STU_FILE, index=False)
                st.success("名單設定已更新！"); st.rerun()

        # --- Tab 4: 自訂課程類別 (全新功能) ---
        with t4:
            st.subheader("⚙️ 自訂課程類別")
            st.info("您可以在這裡新增、修改或刪除課程名稱。所有下拉選單都會自動更新！")
            
            edited_cat = st.data_editor(
                df_cat,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "類別名稱": st.column_config.TextColumn("課程名稱", required=True)
                }
            )
            
            if st.button("💾 儲存課程設定"):
                edited_cat.to_csv(CAT_FILE, index=False)
                st.success("課程列表已更新！現在您可以去排這些新課程了。")
                st.rerun()

        with t5:
            st.dataframe(df_req, use_container_width=True)
            if st.button("🗑️ 清空留言"):
                pd.DataFrame(columns=["日期", "時間", "姓名", "留言"]).to_csv(REQ_FILE, index=False)
                st.rerun()
                
    elif pwd != "":
        st.sidebar.error("密碼錯誤")

if st.sidebar.button("⚠️ 重置系統"):
    for f in [DB_FILE, REQ_FILE, STU_FILE, CAT_FILE]:
        if os.path.exists(f): os.remove(f)
    st.rerun()
