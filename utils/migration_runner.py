"""utils/migration_runner.py — Ejecuta migrations/*.sql pendientes al arrancar la app.

Flujo:
1. Crea schema_migrations si no existe.
2. Escanea migrations/*.sql, ordena por número de versión.
3. Ejecuta solo las versiones no registradas, cada una en su propia transacción.
4. Si una falla: rollback de esa, log del error, detiene las siguientes.
5. Idempotente y silencioso cuando no hay pendientes.

migration_v14.sql: tiene WHERE defensivo (visibilidad='publico') → es idempotente.
Se ejecuta normalmente; el runner la marca como ejecutada en schema_migrations.
"""
import os
import re
import streamlit as st
from sqlalchemy import text
from utils.db import engine

_MIGRATIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "migrations")

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version     INTEGER PRIMARY KEY,
    filename    TEXT        NOT NULL,
    executed_at TIMESTAMPTZ DEFAULT now()
);
"""


def _get_version(filename: str) -> int | None:
    m = re.search(r"migration_v(\d+)", filename)
    return int(m.group(1)) if m else None


def run_pending_migrations() -> list[str]:
    """Ejecuta todas las migrations SQL pendientes. Retorna lista de versiones ejecutadas."""
    if not os.path.isdir(_MIGRATIONS_DIR):
        return []

    executed: list[str] = []

    with engine.begin() as conn:
        conn.execute(text(_CREATE_TABLE))
        already_done = {
            row[0]
            for row in conn.execute(text("SELECT version FROM schema_migrations")).fetchall()
        }

    sql_files = sorted(
        [f for f in os.listdir(_MIGRATIONS_DIR) if f.endswith(".sql")],
        key=lambda f: _get_version(f) or 0,
    )

    for filename in sql_files:
        version = _get_version(filename)
        if version is None or version in already_done:
            continue

        path = os.path.join(_MIGRATIONS_DIR, filename)
        sql = open(path, encoding="utf-8").read()

        # Filtrar comentarios y líneas vacías para no ejecutar sentencias vacías
        statements = [s.strip() for s in sql.split(";") if s.strip() and not s.strip().startswith("--")]

        try:
            with engine.begin() as conn:
                for stmt in statements:
                    if stmt:
                        conn.execute(text(stmt))
                conn.execute(
                    text("INSERT INTO schema_migrations (version, filename) VALUES (:v, :f)"),
                    {"v": version, "f": filename},
                )
            msg = f"migration_runner: v{version} ({filename}) ejecutada ✓"
            print(msg)
            st.toast(msg, icon="✅")
            executed.append(filename)
        except Exception as e:
            msg = f"migration_runner: ERROR en v{version} ({filename}): {e}"
            print(msg)
            st.error(msg)
            break  # No ejecutar las siguientes

    return executed
