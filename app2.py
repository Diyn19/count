from flask import Flask, render_template, request
import sqlite3
from datetime import datetime

app = Flask(__name__)

def calculate(contract, curr_color, prev_color, curr_bw, prev_bw):
    color_pages = curr_color - prev_color
    bw_pages = curr_bw - prev_bw

    color_after_error = max(0, color_pages - int(color_pages * contract["color_error_rate"]))
    bw_after_error = max(0, bw_pages - int(bw_pages * contract["bw_error_rate"]))

    color_after_giveaway = max(0, color_after_error - contract["color_giveaway"])
    bw_after_giveaway = max(0, bw_after_error - contract["bw_giveaway"])

    color_charge_pages = max(0, color_after_giveaway - contract["color_basic"])
    bw_charge_pages = max(0, bw_after_giveaway - contract["bw_basic"])

    color_amount = color_charge_pages * contract["color_unit_price"]
    bw_amount = bw_charge_pages * contract["bw_unit_price"]
    subtotal = contract["monthly_rent"] + color_amount + bw_amount
    tax = subtotal * 0.05
    total = subtotal + tax

    return {
        "彩色列印量": color_pages,
        "黑白列印量": bw_pages,
        "彩色收費張數": color_charge_pages,
        "黑白收費張數": bw_charge_pages,
        "彩色金額": color_amount,
        "黑白金額": bw_amount,
        "月租金": contract["monthly_rent"],
        "未稅金額": subtotal,
        "稅額": tax,
        "含稅總額": total
    }

def get_contract(device_id):
    conn = sqlite3.connect("billing.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM contracts WHERE device_id=?", (device_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def get_last_record(device_id):
    conn = sqlite3.connect("billing.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM meter_records WHERE device_id=? ORDER BY id DESC LIMIT 1", (device_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def add_record(device_id, curr_color, curr_bw):
    conn = sqlite3.connect("billing.db")
    c = conn.cursor()
    month = datetime.now().strftime("%Y-%m")
    c.execute("INSERT INTO meter_records (device_id, month, curr_color, curr_bw) VALUES (?, ?, ?, ?)",
              (device_id, month, curr_color, curr_bw))
    conn.commit()
    conn.close()

@app.route("/", methods=["GET", "POST"])
def index():
    contract = None
    last_color = 0
    last_bw = 0
    result = None

    if request.method == "POST":
        mode = request.form.get("mode")
        device_id = request.form["device_id"]

        contract = get_contract(device_id)
        if not contract:
            return f"❌ 找不到設備 {device_id}"

        last_record = get_last_record(device_id)
        if last_record:
            last_color = last_record["curr_color"]
            last_bw = last_record["curr_bw"]

        # 第二階段：計算
        if mode == "calculate":
            curr_color = int(request.form["curr_color"])
            curr_bw = int(request.form["curr_bw"])
            add_record(device_id, curr_color, curr_bw)
            result = calculate(contract, curr_color, last_color, curr_bw, last_bw)

    return render_template("index.html",
                           contract=contract,
                           last_color=last_color,
                           last_bw=last_bw,
                           result=result)


if __name__ == "__main__":
    app.run(debug=True)
