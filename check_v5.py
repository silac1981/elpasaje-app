import sqlite3

con = sqlite3.connect("elpasaje_v2.db")
cur = con.cursor()

tablas = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print("Tablas:", tablas)
print()

cols_orders = [r[1] for r in cur.execute("PRAGMA table_info(orders)").fetchall()]
print("Cols orders:", cols_orders)
print()

if "pagos" in tablas:
    cols_pagos = [r[1] for r in cur.execute("PRAGMA table_info(pagos)").fetchall()]
    print("Cols pagos:", cols_pagos)
else:
    print("FALTA: tabla pagos no existe — corre migration_v5.py")

if "lineas_config" in tablas:
    cols_lc = [r[1] for r in cur.execute("PRAGMA table_info(lineas_config)").fetchall()]
    print("Cols lineas_config:", cols_lc)
else:
    print("INFO: lineas_config no existe en esta DB")

con.close()
