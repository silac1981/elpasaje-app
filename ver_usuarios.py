import sqlite3
c = sqlite3.connect('elpasaje_v2.db')
for r in c.execute("SELECT * FROM tenants LIMIT 5"):
    print(r)