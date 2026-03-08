#!/usr/bin/env python3
"""Genera backup timestamp de SQLite."""
from __future__ import annotations
import shutil
from datetime import datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "elpasaje.db"
BACKUP_DIR = ROOT / "backups"

def main() -> int:
    print("== Backup SQLite ==")
    if not DB_PATH.exists():
        print("[FAIL] No existe database/elpasaje.db"); return 1
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = BACKUP_DIR / f"elpasaje_{ts}.db"
    shutil.copy2(DB_PATH, target)
    print(f"[OK] Backup generado: {target.relative_to(ROOT)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
