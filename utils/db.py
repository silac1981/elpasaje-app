"""utils/db.py — motor SQLAlchemy compartido por todos los módulos."""
import os
from sqlalchemy import create_engine, event

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "elpasaje_v2.db")
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})


@event.listens_for(engine, "connect")
def _set_pragma(dbapi_conn, _):
    cur = dbapi_conn.cursor()
    cur.execute("PRAGMA foreign_keys=ON")
    cur.close()
