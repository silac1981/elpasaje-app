"""utils/db.py — Motor SQLAlchemy compartido. Soporta SQLite (local) y PostgreSQL (Supabase)."""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, event

load_dotenv()

def _get_database_url() -> str:
    """Retorna DATABASE_URL desde Streamlit secrets (solo en runtime real), .env, o SQLite."""
    # Solo usar st.secrets si Streamlit está corriendo como servidor (no en scripts directos)
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        if get_script_run_ctx() is not None:
            import streamlit as st
            url = st.secrets.get("DATABASE_URL", "")
            if url:
                return url
    except Exception:
        pass
    url = os.environ.get("DATABASE_URL", "")
    if url:
        return url
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "elpasaje_v2.db")
    return f"sqlite:///{db_path}"

_db_url = _get_database_url()
dialect = "postgresql" if _db_url.startswith("postgresql") else "sqlite"

if dialect == "postgresql":
    engine = create_engine(_db_url, pool_pre_ping=True)
else:
    engine = create_engine(_db_url, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def _set_pragma(dbapi_conn, _):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()
