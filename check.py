import sqlite3

conn = sqlite3.connect("billing.db")
c = conn.cursor()

# 建立表格（如果不存在）
c.execute("""CREATE TABLE IF NOT EXISTS contracts (
    device_id TEXT PRIMARY KEY,
    monthly_rent REAL,
    color_unit_price REAL,
    bw_unit_price REAL,
    color_giveaway INTEGER,
    bw_giveaway INTEGER,
    color_error_rate REAL,
    bw_error_rate REAL,
    color_basic INTEGER,
    bw_basic INTEGER
)""")

c.execute("""CREATE TABLE IF NOT EXISTS meter_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT,
    month TEXT,
    curr_color INTEGER,
    curr_bw INTEGER
)""")

# 插入測試契約
c.execute("INSERT OR REPLACE INTO contracts VALUES (?,?,?,?,?,?,?,?,?,?)", (
    "DEV001", 1000, 3.0, 0.5, 50, 100, 0.02, 0.01, 200, 500
))

conn.commit()
conn.close()
print("✅ 已新增測試契約 DEV001")
