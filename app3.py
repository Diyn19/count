import pandas as pd

# === 檔案設定 ===
input_file = "原始資料2.xlsx"
output_file = "資料整理.xlsx"

# 讀取整份 Excel，不設定欄名
df = pd.read_excel(input_file, header=None, dtype=str)
df = df.fillna("")

keep_rows = set()  # 要保留的列索引

for i in range(len(df)):
    row_text = " ".join(df.iloc[i].astype(str)).strip()

    # 如果這列開頭有 T2 或含有關鍵字
    if row_text.startswith("T2") or "設備號碼" in row_text:
        keep_rows.add(i)

    # 如果有「合約期限」，也把它和下兩行都保留
    if "合約期限" in row_text:
        keep_rows.add(i)
        if i + 1 < len(df):
            keep_rows.add(i + 1)
        if i + 2 < len(df):
            keep_rows.add(i + 2)

# 根據保留行建立新資料集（順序不變）
df_out = df.loc[sorted(list(keep_rows))]

# 輸出成新 Excel
df_out.to_excel(output_file, index=False, header=False)

print(f"✅ 已完成篩選，輸出檔案：{output_file}")
