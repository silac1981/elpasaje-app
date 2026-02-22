"""Backup simple de la base SQLite de El Pasaje."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys

DB = Path('database/elpasaje.db')
BACKUP_DIR = Path('backups')


def main() -> int:
    if not DB.exists():
        print(f'ERROR: no existe base de datos en {DB}')
        return 1

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    target = BACKUP_DIR / f'elpasaje_{timestamp}.db'
    shutil.copy2(DB, target)
    print(f'OK backup generado: {target}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
