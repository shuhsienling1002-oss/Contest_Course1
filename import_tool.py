import pandas as pd
import os
from datetime import datetime, date

# 檔案名稱設定 (請確認檔案名稱與您電腦上的一模一樣)
SOURCE_FILE = "2025-2月 教練 林芸  學員排課表.xlsx - 2025-02.csv"
OUTPUT_DB = "schedule_database.csv"

def process_feb_schedule():
    print(f"📂 正在讀取檔案：{SOURCE_FILE} ...")
    
    if not os.path.exists(SOURCE_FILE):
        print(f"❌ 找不到檔案！請確認 {SOURCE_FILE} 是否在資料夾中。")
        return

    try:
        # 1. 讀取 CSV
        # 關鍵修正：Excel轉出的CSV通常標頭在第2行 (index 1)，且編碼可能是 utf-8 或 cp950
        try:
            df = pd.read_csv(SOURCE_FILE, header=1, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(SOURCE_FILE, header=1, encoding='cp950') # 嘗試 Windows 編碼

        # 2. 找出時間欄位 (篩選出長得像 "07:00:00" 的欄位)
        time_cols = [col for col in df.columns if ":" in str(col) and len(str(col)) >= 5]
        print(f"⏰ 偵測到時間欄位：{time_cols[:3]} ... {time_cols[-1]}")

        # 3. 建立資料庫清單
        db_data = []
        
        # 遍歷每一列 (每一天)
        for index, row in df.iterrows():
            # 抓取日期欄位 (通常是第一欄，名稱可能叫 "02月")
            day_str = str(row.iloc[0]) 
            
            # 判斷是否為有效日期行 (例如 "1號", "2號")
            if "號" in day_str:
                try:
                    # 提取數字： "1號" -> 1
                    day_num = int(''.join(filter(str.isdigit, day_str)))
                    current_date = date(2025, 2, day_num) # 設定為 2025年 2月
                    
                    # 遍歷該天的所有時間格
                    for time in time_cols:
                        student_name = row[time]
                        
                        # 如果格子有寫字 (不是 NaN 且不為空)
                        if pd.notna(student_name) and str(student_name).strip() != "":
                            # 排除掉一些奇怪的備註 (例如 "休")
                            clean_name = str(student_name).strip()
                            if clean_name not in ["nan", "休", ""]:
                                db_data.append({
                                    "Date": current_date,
                                    "Time": time[:5], # 只取 07:00
                                    "Student": clean_name,
                                    "Status": "Confirmed"
                                })
                except ValueError:
                    continue # 跳過無法解析日期的行

        # 4. 存檔
        new_df = pd.DataFrame(db_data)
        new_df.to_csv(OUTPUT_DB, index=False, encoding='utf-8-sig') # 加上 sig 讓 Excel 開啟不亂碼
        
        print(f"🎉 成功匯入！共 {len(new_df)} 堂課程。")
        print(f"💾 已儲存為資料庫檔案：{OUTPUT_DB}")
        print("➡️ 現在您可以執行 gym_app.py 了！")
        
        # 顯示前幾筆給您檢查
        print("\n--- 匯入資料預覽 ---")
        print(new_df.head())

    except Exception as e:
        print(f"❌ 發生錯誤：{e}")

if __name__ == "__main__":
    process_feb_schedule()