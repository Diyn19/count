import sqlite3

conn = sqlite3.connect("billing.db")
c = conn.cursor()

c.execute("PRAGMA table_info(contracts);")
columns = c.fetchall()

for col in columns:
    print(col)

conn.close()
