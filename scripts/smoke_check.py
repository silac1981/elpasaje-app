"""Smoke checks locales para validar setup mínimo del proyecto."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

MIN_REQUIRED_VERSION = '2.0 Enterprise'
LEGACY_SIGNATURE = 'VERSION = "1.0 Enterprise"'


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

    app_text = Path('elpasaje_v1.py').read_text(encoding='utf-8', errors='ignore')
    if LEGACY_SIGNATURE in app_text:
        print('ERROR detectada versión legacy de la app (1.0 Enterprise).')
        print('Acción: reemplazar el archivo local por la versión actual del repo (2.0 Enterprise).')
        return 1

    if MIN_REQUIRED_VERSION not in app_text:
        print('WARNING no se pudo confirmar la cadena de versión mínima esperada (2.0 Enterprise).')
        print('Verificá que estás ejecutando el archivo correcto: ./elpasaje_v1.py de esta copia del repo.')

    print('OK smoke_check finalizado')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
