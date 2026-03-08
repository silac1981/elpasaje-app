#!/usr/bin/env python3
"""Inicializa base y deja semillas listas sin UI manual."""
from __future__ import annotations
import runpy
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def main() -> int:
    app_path = ROOT / "elpasaje_v1.py"
    if not app_path.exists():
        print("[FAIL] No se encuentra elpasaje_v1.py"); return 1
    print("== Primer arranque ==")
    print("Inicializando base de datos/semillas importando app...")
    try: runpy.run_path(str(app_path), run_name="__main__")
    except Exception as exc: print(f"[WARN] La app se ejecutó parcialmente (esperable fuera de streamlit): {exc}")
    db_file = ROOT / "database" / "elpasaje.db"
    if db_file.exists():
        print(f"[OK] Base lista: {db_file}"); return 0
    print("[FAIL] No se creó database/elpasaje.db"); return 1

if __name__ == "__main__":
    raise SystemExit(main())
