import sqlite3
c = sqlite3.connect('elpasaje_v2.db')
for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'"):
    print(r[0])