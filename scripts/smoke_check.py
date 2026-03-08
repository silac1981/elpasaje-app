#!/usr/bin/env python3
"""Smoke test compatible con esquema nuevo y legado."""
from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "elpasaje.db"

def fail(msg: str) -> int:
    print(f"[FAIL] {msg}")
    return 1

def table_exists(cur, name: str) -> bool:
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
    return cur.fetchone() is not None

def main() -> int:
    print("== Smoke check ==")
    if not DB_PATH.exists():
        return fail("No existe database/elpasaje.db. Ejecutar streamlit primero.")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Tablas base siempre requeridas
    base_required = ["clientes"]
    for t in base_required:
        if not table_exists(cur, t):
            conn.close()
            return fail(f"Falta la tabla base: {t}")
        print(f"[OK] Tabla encontrada: {t}")

    # Esquema nuevo
    new_schema = ["productos", "stl_proyectos", "ordenes", "orden_items", "materiales", "cotizaciones", "audit_logs", "leads_contacto"]
    # Esquema legado
    old_schema = ["productos_frecuentes", "proyectos_stl", "pedidos", "inventario_materiales"]

    has_new = all(table_exists(cur, t) for t in new_schema)
    has_old = all(table_exists(cur, t) for t in old_schema)

    if not has_new and not has_old:
        conn.close()
        return fail("No coincide ni con esquema nuevo ni con legado.")

    if has_new:
        print("[OK] Esquema detectado: NUEVO")
        productos_table = "productos"
        proyectos_table = "stl_proyectos"
        stock_col = "stock"
    else:
        print("[OK] Esquema detectado: LEGADO")
        productos_table = "productos_frecuentes"
        proyectos_table = "proyectos_stl"
        stock_col = "stock_disponible"

    cur.execute("SELECT COUNT(*) FROM clientes")
    print(f"[OK] clientes={cur.fetchone()[0]}")

    cur.execute(f"SELECT COUNT(*) FROM {productos_table}")
    print(f"[OK] {productos_table}={cur.fetchone()[0]}")

    cur.execute(f"SELECT COUNT(*) FROM {proyectos_table}")
    print(f"[OK] {proyectos_table}={cur.fetchone()[0]}")

    # Validación mínima stock no negativo si columna existe
    cur.execute(f"PRAGMA table_info({productos_table})")
    cols = [r[1] for r in cur.fetchall()]
    if stock_col in cols:
        cur.execute(f"SELECT COUNT(*) FROM {productos_table} WHERE {stock_col} < 0")
        bad = cur.fetchone()[0]
        if bad > 0:
            conn.close()
            return fail(f"Hay {bad} filas con stock negativo en {productos_table}")
        print(f"[OK] Stock válido en {productos_table}")

    conn.close()
    print("RESULTADO: OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
