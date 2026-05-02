import sqlite3, hashlib
c = sqlite3.connect('elpasaje_v2.db')
usuarios = c.execute('SELECT id, password FROM tenants').fetchall()
for uid, pwd in usuarios:
    h = hashlib.sha256(pwd.encode()).hexdigest()
    c.execute('UPDATE tenants SET password=? WHERE id=?', (h, uid))
    print(uid, 'OK')
c.commit()
print('Listo')
