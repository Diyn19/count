from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

app = Flask(__name__)
DB_FILE = "billing.db"

# 初始化資料庫（若無則建立）
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
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
    
    conn.commit()
    conn.close()

# 取得契約
def get_contract(device_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM contracts WHERE device_id=?", (device_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "device_id": row[0],
            "monthly_rent": row[1],
            "color_unit_price": row[2],
            "bw_unit_price": row[3],
            "color_giveaway": row[4],
            "bw_giveaway": row[5],
            "color_error_rate": row[6],
            "bw_error_rate": row[7],
            "color_basic": row[8],
            "bw_basic": row[9]
        }
    return None

# 取得客戶資料
def get_customer(device_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM customers WHERE device_id=?", (device_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "device_id": row[0],
            "customer_name": row[1],
            "device_number": row[2],
            "machine_model": row[3],
            "tax_id": row[4],
            "install_address": row[5],
            "service_person": row[6],
            "contract_number": row[7],
            "contract_start": row[8],
            "contract_end": row[9]
        }
    return None

# 取得最後一筆抄表（前次張數與時間）
def get_last_counts(device_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT color_count, bw_count, timestamp FROM usage WHERE device_id=? ORDER BY id DESC LIMIT 1", (device_id,))
    row = c.fetchone()
    conn.close()
    if row:
        last_time = row[2] if row[2] else ""
        return row[0] or 0, row[1] or 0, last_time
    return 0, 0, ""

# 插入/紀錄本月抄表
def insert_usage(device_id, color_count, bw_count):
    month = datetime.now().strftime("%Y%m")
    timestamp = datetime.now().strftime("%Y/%m/%d-%H:%M")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO usage (device_id, month, color_count, bw_count, timestamp) VALUES (?, ?, ?, ?, ?)",
              (device_id, month, color_count, bw_count, timestamp))
    conn.commit()
    conn.close()

# 計算邏輯（返回結果 dict）
def calculate(contract, curr_color, curr_bw, last_color, last_bw):
    used_color = max(0, curr_color - last_color)
    used_bw = max(0, curr_bw - last_bw)

    # 扣贈送
    bill_color = max(0, used_color - contract["color_giveaway"])
    bill_bw = max(0, used_bw - contract["bw_giveaway"])

    # 誤印率調整
    bill_color = int(round(bill_color * (1 - contract["color_error_rate"])))
    bill_bw = int(round(bill_bw * (1 - contract["bw_error_rate"])))

    # 基本張數
    if contract["color_basic"] and contract["color_basic"] > 0:
        bill_color = max(contract["color_basic"], bill_color)
    if contract["bw_basic"] and contract["bw_basic"] > 0:
        bill_bw = max(contract["bw_basic"], bill_bw)

    # 金額
    color_amount = bill_color * contract["color_unit_price"]
    bw_amount = bill_bw * contract["bw_unit_price"]
    subtotal = contract["monthly_rent"] + color_amount + bw_amount

    tax_rate = 0.05
    tax = subtotal * tax_rate
    total = subtotal + tax

    return {
        "彩色使用張數": used_color,
        "黑白使用張數": used_bw,
        "彩色計費張數": bill_color,
        "黑白計費張數": bill_bw,
        "彩色金額": round(color_amount, 2),
        "黑白金額": round(bw_amount, 2),
        "月租金": round(contract["monthly_rent"], 2),
        # 🔽 這三個四捨五入到整數
        "未稅小計": int(round(subtotal)),
        "稅額": int(round(tax)),
        "含稅總額": int(round(total))
    }

@app.route("/", methods=["GET", "POST"])
def index():
    message = request.args.get("message", "")
    contract = None
    customer = None
    last_color, last_bw, last_time = 0, 0, ""
    result = None

    if request.method == "POST":
        mode = request.form.get("mode")
        
        if mode == "query":
            device_id = request.form.get("device_id", "").strip()
            contract = get_contract(device_id)
            customer = get_customer(device_id)
            if not contract:
                message = f"❌ 找不到設備 {device_id}"
            else:
                last_color, last_bw, last_time = get_last_counts(device_id)

        elif mode == "calculate":
            device_id = request.form.get("device_id", "").strip()
            contract = get_contract(device_id)
            customer = get_customer(device_id)
            if not contract:
                message = f"❌ 找不到設備 {device_id}"
            else:
                last_color, last_bw, last_time = get_last_counts(device_id)
                try:
                    curr_color = int(request.form.get("curr_color", "0"))
                    curr_bw = int(request.form.get("curr_bw", "0"))
                except Exception as e:
                    message = f"輸入格式錯誤: {e}"
                else:
                    result = calculate(contract, curr_color, curr_bw, last_color, last_bw)
                    insert_usage(device_id, curr_color, curr_bw)

        elif mode == "update_contract":
            device_id = request.form.get("device_id", "").strip()
            try:
                monthly_rent = float(request.form.get("monthly_rent", "0") or "0")
                color_unit_price = float(request.form.get("color_unit_price", "0") or "0")
                bw_unit_price = float(request.form.get("bw_unit_price", "0") or "0")
                color_giveaway = int(request.form.get("color_giveaway", "0") or "0")
                bw_giveaway = int(request.form.get("bw_giveaway", "0") or "0")
                color_error_rate = float(request.form.get("color_error_rate", "0") or "0")
                bw_error_rate = float(request.form.get("bw_error_rate", "0") or "0")
                color_basic = int(request.form.get("color_basic", "0") or "0")
                bw_basic = int(request.form.get("bw_basic", "0") or "0")
            except Exception as e:
                message = f"讀取表單欄位錯誤: {e}"
            else:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("""UPDATE contracts SET
                             monthly_rent=?, color_unit_price=?, bw_unit_price=?,
                             color_giveaway=?, bw_giveaway=?, color_error_rate=?, bw_error_rate=?,
                             color_basic=?, bw_basic=? WHERE device_id=?""",
                          (monthly_rent, color_unit_price, bw_unit_price,
                           color_giveaway, bw_giveaway, color_error_rate, bw_error_rate,
                           color_basic, bw_basic, device_id))
                conn.commit()
                conn.close()
                return redirect(url_for("index", device_id=device_id, message="✅ 契約條件已更新"))

    else:
        q_device = request.args.get("device_id")
        if q_device:
            contract = get_contract(q_device)
            customer = get_customer(q_device)
            if contract:
                last_color, last_bw, last_time = get_last_counts(q_device)
            else:
                message = f"❌ 找不到設備 {q_device}"

    return render_template("index.html",
                           contract=contract,
                           customer=customer,
                           last_color=last_color,
                           last_bw=last_bw,
                           last_time=last_time,
                           result=result,
                           message=message)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=10000)

