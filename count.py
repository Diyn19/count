import tkinter as tk
from tkinter import messagebox


class PrintBillingCalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("列印計費計算器")

        # 輸入欄位設定
        self.entries = {}
        fields = [
            ("月租金", 1000),
            ("稅率(小數)", 0.05),
            ("彩色單價", 3.0),
            ("黑白單價", 0.5),
            ("彩色贈送張數", 50),
            ("黑白贈送張數", 100),
            ("彩色誤印率", 0.02),
            ("黑白誤印率", 0.01),
            ("彩色基本張數", 200),
            ("黑白基本張數", 500),
            ("本月彩色", 1200),
            ("前次彩色", 1000),
            ("本月黑白", 5300),
            ("前次黑白", 5000),
        ]

        for i, (label, default) in enumerate(fields):
            tk.Label(root, text=label, anchor="w", width=20).grid(row=i, column=0, padx=5, pady=2, sticky="w")
            entry = tk.Entry(root, width=15)
            entry.grid(row=i, column=1, padx=5, pady=2)
            entry.insert(0, str(default))
            self.entries[label] = entry

        # 稅別選擇
        self.tax_mode = tk.StringVar(value="untaxed")
        tk.Label(root, text="計算模式:").grid(row=len(fields), column=0, sticky="w", padx=5, pady=2)
        tk.Radiobutton(root, text="未稅計算", variable=self.tax_mode, value="untaxed").grid(row=len(fields), column=1, sticky="w")
        tk.Radiobutton(root, text="含稅計算", variable=self.tax_mode, value="taxed").grid(row=len(fields)+1, column=1, sticky="w")

        # 計算按鈕
        tk.Button(root, text="計算", command=self.calculate).grid(row=len(fields)+2, column=0, columnspan=2, pady=10)

    def calculate(self):
        try:
            # 讀取輸入
            monthly_rent = float(self.entries["月租金"].get())
            tax_rate = float(self.entries["稅率(小數)"].get())
            color_unit_price = float(self.entries["彩色單價"].get())
            bw_unit_price = float(self.entries["黑白單價"].get())
            color_giveaway = int(self.entries["彩色贈送張數"].get())
            bw_giveaway = int(self.entries["黑白贈送張數"].get())
            color_error_rate = float(self.entries["彩色誤印率"].get())
            bw_error_rate = float(self.entries["黑白誤印率"].get())
            color_basic = int(self.entries["彩色基本張數"].get())
            bw_basic = int(self.entries["黑白基本張數"].get())
            curr_color = int(self.entries["本月彩色"].get())
            prev_color = int(self.entries["前次彩色"].get())
            curr_bw = int(self.entries["本月黑白"].get())
            prev_bw = int(self.entries["前次黑白"].get())

            # 計算
            color_pages = curr_color - prev_color
            bw_pages = curr_bw - prev_bw

            color_after_error = max(0, color_pages - int(color_pages * color_error_rate))
            bw_after_error = max(0, bw_pages - int(bw_pages * bw_error_rate))

            color_after_giveaway = max(0, color_after_error - color_giveaway)
            bw_after_giveaway = max(0, bw_after_error - bw_giveaway)

            color_charge_pages = max(0, color_after_giveaway - color_basic)
            bw_charge_pages = max(0, bw_after_giveaway - bw_basic)

            color_amount = color_charge_pages * color_unit_price
            bw_amount = bw_charge_pages * bw_unit_price
            subtotal = monthly_rent + color_amount + bw_amount

            # 稅額與含稅計算
            if self.tax_mode.get() == "untaxed":
                tax = subtotal * tax_rate
                total = subtotal + tax
                calc_mode = "未稅 → 含稅"
            else:  # 含稅條件計算
                total = subtotal
                subtotal = subtotal / (1 + tax_rate)
                tax = total - subtotal
                calc_mode = "含稅 → 未稅拆分"

            # 結果輸出
            result = (
                f"計算模式: {calc_mode}\n\n"
                f"彩色列印量: {color_pages}\n"
                f"黑白列印量: {bw_pages}\n"
                f"彩色收費張數: {color_charge_pages}\n"
                f"黑白收費張數: {bw_charge_pages}\n"
                f"彩色金額: {color_amount:.2f}\n"
                f"黑白金額: {bw_amount:.2f}\n"
                f"月租金: {monthly_rent:.2f}\n"
                f"未稅金額: {subtotal:.2f}\n"
                f"稅額: {tax:.2f}\n"
                f"含稅總額: {total:.2f}"
            )

            messagebox.showinfo("計算結果", result)

        except Exception as e:
            messagebox.showerror("錯誤", f"輸入格式錯誤: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = PrintBillingCalculatorApp(root)
    root.mainloop()
