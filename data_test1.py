import sqlite3

conn = sqlite3.connect("billing.db")
c = conn.cursor()

# --- 建立 contracts 表（若尚未建立），新增 tax_type 欄位 ---
c.execute("""
CREATE TABLE IF NOT EXISTS contracts (
    device_id TEXT PRIMARY KEY,
    monthly_rent REAL,
    color_unit_price REAL,
    bw_unit_price REAL,
    color_giveaway INTEGER,
    bw_giveaway INTEGER,
    color_error_rate REAL,
    bw_error_rate REAL,
    color_basic INTEGER,
    bw_basic INTEGER,
    tax_type TEXT DEFAULT '含稅'  -- 新增稅別欄位
)
""")

# --- 建立 customers 表 ---
c.execute("""
CREATE TABLE IF NOT EXISTS customers (
    device_id TEXT PRIMARY KEY,
    customer_name TEXT,
    device_number TEXT,
    machine_model TEXT,
    tax_id TEXT,
    install_address TEXT,
    service_person TEXT,
    contract_number TEXT,
    contract_start TEXT,
    contract_end TEXT
)
""")

# --- 契約資料 (加入 tax_type) ---
c.execute("""
INSERT OR REPLACE INTO contracts VALUES (
    'DEV001', 1000, 3.0, 0.5, 50, 100, 0.02, 0.01, 200, 500, '含稅'
)
""")
c.execute("""
INSERT OR REPLACE INTO contracts VALUES (
    'DEV002', 1500, 2.8, 0.6, 80, 200, 0.015, 0.02, 300, 600, '未稅'
)
""")

# --- 客戶資料 ---
c.execute("""
INSERT OR REPLACE INTO customers VALUES (
    'DEV001', '張三有限公司', 'A12345', 'Canon iR-ADV', '12345678',
    '台北市信義區信義路1號', '王小明', 'C001', '2024/01/01', '2025/12/31'
)
""")
c.execute("""
INSERT OR REPLACE INTO customers VALUES (
    'DEV002', '李四企業', 'B67890', 'Ricoh MP C4504', '87654321',
    '台北市大安區復興南路2號', '陳小華', 'C002', '2024/03/01', '2026/02/28'
)
""")

conn.commit()
conn.close()
print("✅ Sample contracts & customers inserted (DEV001 & DEV002) with tax_type!")
