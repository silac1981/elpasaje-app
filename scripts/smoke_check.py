"""Smoke checks locales para validar setup mínimo del proyecto."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REQUIRED_FILES = [
    Path('elpasaje_v1.py'),
    Path('requirements.txt'),
    Path('.env.example'),
    Path('docs/QA_CHECKLIST.md'),
    Path('docs/DEPLOY_RUNBOOK.md'),
]


def run(cmd: list[str]) -> int:
    print('>>', ' '.join(cmd))
    return subprocess.run(cmd, check=False).returncode


def main() -> int:
    missing = [str(p) for p in REQUIRED_FILES if not p.exists()]
    if missing:
        print('ERROR faltan archivos:', ', '.join(missing))
        return 1

    code = run([sys.executable, '-m', 'py_compile', 'elpasaje_v1.py'])
    if code != 0:
        print('ERROR py_compile falló')
        return code

    print('OK smoke_check finalizado')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
