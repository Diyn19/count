import sqlite3

def init_db():
    conn = sqlite3.connect("billing.db")
    c = conn.cursor()

    # 契約/設備表
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
        bw_basic INTEGER
    )
    """)

    # 抄表紀錄表
    c.execute("""
    CREATE TABLE IF NOT EXISTS meter_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id TEXT,
        month TEXT,               -- 格式 2025-10
        curr_color INTEGER,
        curr_bw INTEGER,
        FOREIGN KEY(device_id) REFERENCES contracts(device_id)
    )
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialized!")

if __name__ == "__main__":
    init_db()
