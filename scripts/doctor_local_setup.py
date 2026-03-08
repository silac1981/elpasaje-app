#!/usr/bin/env python3
"""Diagnóstico local rápido para El Pasaje App."""
from __future__ import annotations
import importlib, sqlite3, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "elpasaje.db"

def check_python() -> bool:
    ok = sys.version_info >= (3, 10)
    print(f"[{'OK' if ok else 'FAIL'}] Python {sys.version.split()[0]} (requerido >=3.10)")
    return ok

def check_deps() -> bool:
    required = ["streamlit", "pandas"]
    missing = []
    for pkg in required:
        try:
            importlib.import_module(pkg); print(f"[OK] Dependencia disponible: {pkg}")
        except Exception:
            missing.append(pkg); print(f"[FAIL] Dependencia faltante: {pkg}")
    return not missing

def check_files() -> bool:
    required_files = [ROOT / "elpasaje_v1.py", ROOT / "requirements.txt", ROOT / "scripts" / "smoke_check.py", ROOT / "scripts" / "backup_sqlite.py"]
    all_ok = True
    for fpath in required_files:
        exists = fpath.exists()
        print(f"[{'OK' if exists else 'FAIL'}] {fpath.relative_to(ROOT)}")
        all_ok = all_ok and exists
    return all_ok

def check_git_context() -> bool:
    git_dir = ROOT / ".git"
    if not git_dir.exists():
        print("[WARN] No se detectó .git en la raíz.")
        return True
    def run(args: list[str]) -> str:
        try: return subprocess.check_output(args, cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
        except Exception: return ""
    branch = run(["git", "branch", "--show-current"])
    remote = run(["git", "remote", "get-url", "origin"])
    print(f"[OK] Git branch: {branch or '(sin branch)'}")
    print(f"[OK] Git origin: {remote or '(sin origin)'}")
    return True

def check_db() -> bool:
    if not DB_PATH.exists():
        print("[WARN] Base de datos no encontrada aún.")
        return True
    try:
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [x[0] for x in cur.fetchall()]; conn.close()
        print(f"[OK] SQLite accesible. Tablas: {', '.join(tables) if tables else '(sin tablas)'}")
        return True
    except Exception as exc:
        print(f"[FAIL] Error accediendo SQLite: {exc}")
        return False

def main() -> int:
    print("== Doctor local setup ==")
    results = [check_python(), check_deps(), check_files(), check_git_context(), check_db()]
    if all(results):
        print("\nRESULTADO: OK - Entorno operativo"); return 0
    print("\nRESULTADO: FAIL - Revisar checks anteriores"); return 1

if __name__ == "__main__":
    raise SystemExit(main())
