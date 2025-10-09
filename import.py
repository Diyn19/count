# import_from_xlsx.py
import sqlite3
import pandas as pd
import os

DB_FILE = "billing.db"
EXCEL_FILE = "import_data.xlsx"


def init_db():
    """建立資料表（若不存在）— contracts 已包含 tax_type 欄位"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS contracts (
        device_id TEXT PRIMARY KEY,
        monthly_rent REAL,
        contra TEXT,
        color_unit_price REAL,
        bw_unit_price REAL,
        color_giveaway INTEGER,
        bw_giveaway INTEGER,
        color_error_rate REAL,
        bw_error_rate REAL,
        color_basic INTEGER,
        bw_basic INTEGER,
        tax_type TEXT DEFAULT '含稅'
    )
    """)
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
    c.execute("""
    CREATE TABLE IF NOT EXISTS usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id TEXT,
        month TEXT,
        color_count INTEGER,
        bw_count INTEGER,
        timestamp TEXT
    )
    """)
    conn.commit()
    conn.close()
    print("✅ DB tables ensured (contracts, customers, usage).")


def _norm_val(v):
    """將 pandas 的 NaN / Timestamp / Decimal 等型別轉成 SQLite 可接受格式"""
    if pd.isna(v):
        return None
    if isinstance(v, pd.Timestamp):
        return v.strftime("%Y/%m/%d")
    if isinstance(v, (int, float, str)):
        return v
    try:
        return str(v)
    except Exception:
        return None


def import_excel_to_db(excel_file=EXCEL_FILE, replace_existing=True):
    """從 Excel 匯入 customers + contracts 到 SQLite"""
    if not os.path.isfile(excel_file):
        raise FileNotFoundError(f"找不到 {excel_file}，請放在同一資料夾或指定正確路徑。")

    print(f"📥 開始讀取 Excel：{excel_file}")
    xls = pd.ExcelFile(excel_file)
    sheet_names = xls.sheet_names
    if "customers" not in sheet_names or "contracts" not in sheet_names:
        raise ValueError("Excel 必須包含 sheet: 'customers' 與 'contracts'（大小寫相同）。")

    df_customers = pd.read_excel(xls, sheet_name="customers", dtype=object)
    df_contracts = pd.read_excel(xls, sheet_name="contracts", dtype=object)

    # 必要欄位
    required_customers = [
        "device_id", "customer_name", "device_number", "machine_model",
        "tax_id", "install_address", "service_person",
        "contract_number", "contract_start", "contract_end"
    ]
    required_contracts = [
        "device_id", "monthly_rent", "color_unit_price", "bw_unit_price",
        "color_giveaway", "bw_giveaway", "color_error_rate", "bw_error_rate",
        "color_basic", "bw_basic", "tax_type","contra"
    ]

    # 欄位檢查
    for col in required_customers:
        if col not in df_customers.columns:
            raise ValueError(f"customers sheet 缺少必要欄位: {col}")

    for col in required_contracts:
        if col not in df_contracts.columns:
            if col == "tax_type":
                print("⚠️ contracts sheet 缺少 tax_type 欄位，將以 '含稅' 作為預設值。")
                df_contracts["tax_type"] = "含稅"
            else:
                raise ValueError(f"contracts sheet 缺少必要欄位: {col}")

    # 清理資料
    df_customers = df_customers.fillna("")
    df_contracts = df_contracts.fillna("")

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # 匯入 customers
    inserted_cust = 0
    skipped_cust = 0
    for _, row in df_customers.iterrows():
        vals = tuple(_norm_val(row.get(col)) for col in required_customers)
        try:
            if replace_existing:
                c.execute("""
                    INSERT OR REPLACE INTO customers (
                        device_id, customer_name, device_number, machine_model,
                        tax_id, install_address, service_person,
                        contract_number, contract_start, contract_end
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, vals)
            else:
                c.execute("""
                    INSERT INTO customers (
                        device_id, customer_name, device_number, machine_model,
                        tax_id, install_address, service_person,
                        contract_number, contract_start, contract_end
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, vals)
            inserted_cust += 1
        except sqlite3.IntegrityError:
            skipped_cust += 1

    # 匯入 contracts
    inserted_cont = 0
    skipped_cont = 0
    for _, row in df_contracts.iterrows():
        def num(col, default=0):
            v = _norm_val(row.get(col))
            if v in [None, ""]:
                return default
            try:
                return float(v)
            except:
                return default

        vals = (
            _norm_val(row.get("device_id")),
            num("monthly_rent", 0),
            num("color_unit_price", 0),
            num("bw_unit_price", 0),
            int(num("color_giveaway", 0)),
            int(num("bw_giveaway", 0)),
            float(num("color_error_rate", 0)),
            float(num("bw_error_rate", 0)),
            int(num("color_basic", 0)),
            int(num("bw_basic", 0)),
            str(_norm_val(row.get("tax_type")) or "含稅"),
            str(_norm_val(row.get("contra")) or "")
        )

        try:
            if replace_existing:
                c.execute("""
                    INSERT OR REPLACE INTO contracts (
                        device_id, monthly_rent, color_unit_price, bw_unit_price,
                        color_giveaway, bw_giveaway, color_error_rate, bw_error_rate,
                        color_basic, bw_basic, tax_type, contra
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?)
                """, vals)
            else:
                c.execute("""
                    INSERT INTO contracts (
                        device_id, monthly_rent, color_unit_price, bw_unit_price,
                        color_giveaway, bw_giveaway, color_error_rate, bw_error_rate,
                        color_basic, bw_basic, tax_type, contra
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?)
                """, vals)
            inserted_cont += 1
        except sqlite3.IntegrityError:
            skipped_cont += 1

    conn.commit()
    conn.close()

    print(f"✅ 匯入完成：customers 新增/覆蓋 {inserted_cust} 筆，contracts 新增/覆蓋 {inserted_cont} 筆。")
    if not replace_existing:
        print(f"（跳過已存在而未覆蓋：customers {skipped_cust} 筆，contracts {skipped_cont} 筆）")


def create_example_excel(filename="import_data.xlsx"):
    """建立一個範本 Excel（customers 與 contracts）"""
    customers = [
        {
            "device_id": "DEV001", "customer_name": "張三有限公司", "device_number": "A12345",
            "machine_model": "Canon iR-ADV", "tax_id": "12345678",
            "install_address": "台北市信義路1號", "service_person": "王小明",
            "contract_number": "C001", "contract_start": "2024/01/01", "contract_end": "2025/12/31"
        },
        {
            "device_id": "DEV002", "customer_name": "李四企業", "device_number": "B67890",
            "machine_model": "Ricoh MP C4504", "tax_id": "87654321",
            "install_address": "台北市大安區復興南路2號", "service_person": "陳小華",
            "contract_number": "C002", "contract_start": "2024/03/01", "contract_end": "2026/02/28"
        }
    ]
    contracts = [
        {
            "device_id": "DEV001", "monthly_rent": 1000, "color_unit_price": 3.0, "bw_unit_price": 0.5,
            "color_giveaway": 50, "bw_giveaway": 100, "color_error_rate": 0.02, "bw_error_rate": 0.01,
            "color_basic": 200, "bw_basic": 500, "tax_type": "含稅"
        },
        {
            "device_id": "DEV002", "monthly_rent": 1500, "color_unit_price": 2.8, "bw_unit_price": 0.6,
            "color_giveaway": 80, "bw_giveaway": 200, "color_error_rate": 0.015, "bw_error_rate": 0.02,
            "color_basic": 300, "bw_basic": 600, "tax_type": "未稅"
        }
    ]
    df1 = pd.DataFrame(customers)
    df2 = pd.DataFrame(contracts)
    with pd.ExcelWriter(filename) as writer:
        df1.to_excel(writer, sheet_name="customers", index=False)
        df2.to_excel(writer, sheet_name="contracts", index=False)
    print(f"✅ 已產生範本檔：{filename}")


if __name__ == "__main__":
    init_db()
    # 若需產生範本 Excel，取消下一行註解
    # create_example_excel("import_data.xlsx")

    # 執行匯入（replace_existing=True 代表會覆蓋相同 device_id）
    import_excel_to_db(EXCEL_FILE, replace_existing=True)
