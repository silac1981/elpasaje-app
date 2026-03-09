# ep_core.py - Núcleo de datos El Pasaje
import sqlite3
import os

def get_db_connection():
    db_path = os.path.join('database', 'elpasaje.db')
    return sqlite3.connect(db_path)

def check_system_integrity():
    return os.path.exists('database/elpasaje.db')
