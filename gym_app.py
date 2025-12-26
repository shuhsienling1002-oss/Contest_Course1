import streamlit as st
import pandas as pd
import os
from datetime import datetime, date, timedelta

# =================設定與常數=================
st.set_page_config(page_title="林芸教練排課系統", page_icon="🧘‍♀️", layout="wide")

# 檔案路徑 (請確保這些檔案在同一個資料夾)
# 原始 CSV 檔名 (依照您上傳的檔案)
SOURCE_CSV = "2025-2月 教練 林芸  學員排課表.xlsx - 2025-02.csv"
# 系統運作用的資料庫 CSV
DB_FILE = "schedule_database.csv"
# 預約留言板
MSG_FILE = "booking_requests.csv"

# 定義時間欄位 (根據您的 Excel 表頭)
TIME_SLOTS = [
    "07:00:00", "08:00:00", "09:00:00", "10:00:00", "11:00:00", "12:00:00", 
    "13:00:00", "14:00:00", "15:00:00", "16:00:00", "17:00:00", "18:00:00", 
    "19:00:00", "20:00:00", "21:00:00", "22:00:00"
]

# =================資料處理函數=================

def init_db():
    """初始化：如果沒有資料庫，從原始 2月 CSV 轉檔建立"""
    if not os.path.exists(DB_FILE):
        if os.path.exists(SOURCE_CSV):
            try:
                # 讀取原始檔
                raw_df = pd.read_csv(SOURCE_CSV)
                
                # 建立空的標準格式清單
                data_list = []
                
                # 簡單的解析邏輯 (針對您的檔案格式)
                # 假設第一欄是日期 '1號', '2號'...
                for index, row in raw_df.iterrows():
                    day_str = str(row.iloc[0]) # 取得日期欄位 (例如 "1號")
                    
                    # 簡單處理日期：假設是 2025年 2月
                    if "號" in day_str:
                        day_num = day_str.replace("號", "").strip()
                        if day_num.isdigit():
                            current_date = date(2025, 2, int(day_num))
                            
                            # 遍歷所有時間欄位
                            for time_col in TIME_SLOTS:
                                if time_col in raw_df.columns:
                                    content = row[time_col]
                                    # 如果格子不是空的，也不是 NaN
                                    if pd.notna(content) and str(content).strip() != "":
                                        data_list.append({
                                            "Date": current_date,
                                            "Time": time_col[:5], # 取 07:00
                                            "Student": str(content).strip(),
                                            "Status": "Confirmed" # 已確認課程
                                        })
                
                # 轉成 DataFrame 並存檔
                new_df = pd.DataFrame(data_list)
                new_df.to_csv(DB_FILE, index=False)
                st.toast("✅ 已成功匯入 2 月份課表！")
                return new_df
            except Exception as e:
                st.error(f"匯入失敗: {e}")
                return pd.DataFrame(columns=["Date", "Time", "Student", "Status"])
        else:
            # 如果連原始檔都沒有，建立空的
            return pd.DataFrame(columns=["Date", "Time", "Student", "Status"])
    else:
        return pd.read_csv(DB_FILE)

def load_schedule():
    df = pd.read_csv(DB_FILE)
    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    return df

def save_schedule(df):
    df.to_csv(DB_FILE, index=False)

def load_requests():
    if not os.path.exists(MSG_FILE):
        return pd.DataFrame(columns=["RequestDate", "TargetDate", "Time", "StudentName", "Note", "Status"])
    return pd.read_csv(MSG_FILE)

def save_requests(df):
    df.to_csv(MSG_FILE, index=False)

# =================主程式邏輯=================

# 初始化資料庫
df_schedule = init_db()

# 側邊欄：身份選擇
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2964/2964514.png", width=100)
st.sidebar.title("功能選單")
role = st.sidebar.radio("請選擇身份", ["👩‍🎓 學員查詢/預約", "🧢 教練排課管理"])

# 日曆選擇器 (共用)
st.sidebar.markdown("---")
st.sidebar.subheader("📅 日曆查詢")
selected_date = st.sidebar.date_input("選擇日期", date(2025, 2, 1))

# ----------------- 學員模式 -----------------
if role == "👩‍🎓 學員查詢/預約":
    st.title(f"🗓️ 課表查詢：{selected_date.strftime('%Y-%m-%d')}")
    
    # 1. 顯示當日課表
    day_schedule = df_schedule[df_schedule["Date"] == selected_date]
    
    # 製作時間軸顯示
    schedule_view = []
    display_times = [t[:5] for t in TIME_SLOTS] # 07:00, 08:00...
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("當日課程狀況")
        if day_schedule.empty:
            st.info("本日目前無任何排課紀錄。")
        else:
            # 顯示表格，美化一下
            st.dataframe(
                day_schedule[["Time", "Student"]].sort_values("Time"),
                use_container_width=True,
                hide_index=True
            )

    # 2. 預約留言區
    with col2:
        st.subheader("💌 預約/候補留言")
        st.caption("想上的時段被約走了？或是有空堂想預約？請在此留言。")
        
        with st.form("booking_form"):
            req_name = st.text_input("您的姓名")
            req_time = st.selectbox("想預約的時段", display_times)
            req_note = st.text_area("備註 (例如：如果要候補，或是想上什麼課)")
            
            submitted = st.form_submit_button("送出預約詢問")
            if submitted:
                if req_name:
                    req_df = load_requests()
                    new_req = pd.DataFrame([{
                        "RequestDate": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "TargetDate": selected_date,
                        "Time": req_time,
                        "StudentName": req_name,
                        "Note": req_note,
                        "Status": "待審核"
                    }])
                    req_df = pd.concat([req_df, new_req], ignore_index=True)
                    save_requests(req_df)
                    st.success("已送出給教練！請等候通知。")
                else:
                    st.warning("請填寫姓名")

# ----------------- 教練模式 -----------------
elif role == "🧢 教練排課管理":
    st.title("🔧 教練後台管理")
    
    tab1, tab2, tab3 = st.tabs(["📝 課表增修", "📩 處理預約", "📊 全月檢視"])
    
    # Tab 1: 單日課表編輯
    with tab1:
        st.subheader(f"編輯日期：{selected_date}")
        
        # 讀取當天資料
        current_day_data = df_schedule[df_schedule["Date"] == selected_date].copy()
        
        # 使用 Data Editor 讓教練直接編輯
        edited_df = st.data_editor(
            current_day_data,
            column_config={
                "Date": st.column_config.DateColumn("日期", disabled=True),
                "Time": st.column_config.SelectboxColumn("時間", options=[t[:5] for t in TIME_SLOTS], required=True),
                "Student": st.column_config.TextColumn("學員/課程內容", required=True),
                "Status": st.column_config.SelectboxColumn("狀態", options=["Confirmed", "Cancelled"])
            },
            num_rows="dynamic", # 允許新增行
            use_container_width=True,
            key="editor"
        )
        
        if st.button("💾 儲存變更"):
            # 1. 刪除舊的這一天資料
            df_schedule = df_schedule[df_schedule["Date"] != selected_date]
            # 2. 補上日期的值 (因為如果是新增的行，Date 可能是空的)
            if not edited_df.empty:
                edited_df["Date"] = selected_date
                # 3. 合併
                df_schedule = pd.concat([df_schedule, edited_df], ignore_index=True)
            
            save_schedule(df_schedule)
            st.success("課表已更新！")

    # Tab 2: 審核預約
    with tab2:
        st.subheader("待處理的學生預約")
        req_df = load_requests()
        
        # 只顯示待審核
        pending_reqs = req_df[req_df["Status"] == "待審核"]
        
        if pending_reqs.empty:
            st.info("目前沒有新留言。")
        else:
            for idx, row in pending_reqs.iterrows():
                with st.expander(f"{row['TargetDate']} {row['Time']} - {row['StudentName']}"):
                    st.write(f"備註: {row['Note']}")
                    c1, c2 = st.columns(2)
                    if c1.button("✅ 核准並加入課表", key=f"app_{idx}"):
                        # 1. 加入主課表
                        new_class = pd.DataFrame([{
                            "Date": datetime.strptime(str(row['TargetDate']), "%Y-%m-%d").date(),
                            "Time": row['Time'],
                            "Student": row['StudentName'],
                            "Status": "Confirmed"
                        }])
                        df_schedule = pd.concat([df_schedule, new_class], ignore_index=True)
                        save_schedule(df_schedule)
                        
                        # 2. 更新請求狀態
                        req_df.at[idx, "Status"] = "已核准"
                        save_requests(req_df)
                        st.experimental_rerun()
                        
                    if c2.button("❌ 婉拒/已溝通", key=f"rej_{idx}"):
                        req_df.at[idx, "Status"] = "已婉拒"
                        save_requests(req_df)
                        st.experimental_rerun()

    # Tab 3: 全月預覽
    with tab3:
        st.subheader("全月份快速檢視")
        # 製作一個樞紐分析表 (Pivot Table) 模擬 Excel 格式
        if not df_schedule.empty:
            # 確保 Date 是 datetime 格式以便排序
            df_view = df_schedule.copy()
            df_view["Date"] = pd.to_datetime(df_view["Date"])
            
            # 篩選月份 (根據側邊欄選擇的日期的月份)
            mask = (df_view['Date'].dt.month == selected_date.month) & (df_view['Date'].dt.year == selected_date.year)
            df_month = df_view[mask]
            
            if not df_month.empty:
                df_month["Day"] = df_month["Date"].dt.day
                pivot_schedule = df_month.pivot(index="Day", columns="Time", values="Student")
                st.dataframe(pivot_schedule, use_container_width=True)
            else:
                st.info("本月尚無資料")
        else:
            st.info("資料庫為空")
            
st.sidebar.markdown("---")
st.sidebar.caption("系統開發：FP-CRF v6.1 | 數據來源：2025-2月 教練 CSV")