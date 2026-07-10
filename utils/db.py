"""utils/db.py — Motor SQLAlchemy compartido. Soporta SQLite (local) y PostgreSQL (Supabase)."""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, event

load_dotenv()

def _get_database_url() -> str:
    """Retorna DATABASE_URL desde .env local o st.secrets (Streamlit Cloud).
    Lanza RuntimeError si no se encuentra — sin fallback silencioso a SQLite.
    """
    url = os.environ.get("DATABASE_URL", "")
    if url:
        return url
    try:
        import streamlit as st
        url = st.secrets.get("DATABASE_URL", "")
        if url:
            return url
    except Exception:
        pass
    raise RuntimeError(
        "DATABASE_URL no configurada. "
        "Local: descomentá DATABASE_URL en .env. "
        "Cloud: configurá el secret en Streamlit Cloud > Settings > Secrets."
    )

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
