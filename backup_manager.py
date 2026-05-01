"""
╔══════════════════════════════════════════════════════════╗
║         BACKUP MANAGER — SIA + EL PASAJE                ║
║         Alejandra Gomez Aguilera                        ║
║         Google Drive + Disco Externo + GitHub           ║
╚══════════════════════════════════════════════════════════╝

MODOS DE USO:
  python backup_manager.py sia          → backup manual SIA
  python backup_manager.py elpasaje     → backup manual El Pasaje
  python backup_manager.py ambos        → backup manual los dos
  python backup_manager.py programar    → activa el backup diario de 20hs (El Pasaje)

INTEGRACIÓN AUTOMÁTICA EN SIA:
  Al final de sap_match_engine, llamar:
      from backup_manager import backup_sia
      backup_sia(motivo="Ejecucion diaria automatica")
"""

import subprocess
import shutil
import os
import sys
import json
from datetime import datetime
from pathlib import Path

# ══════════════════════════════════════════════════════
# CONFIGURACIÓN — EDITÁ ESTAS RUTAS SI ES NECESARIO
# ══════════════════════════════════════════════════════

CONFIG = {
    "SIA": {
        "repo_path":      r"C:\Trabajo\SIA_Project",
        "branch":         "main",
        "google_drive":   r"C:\Users\ar028883\Google Drive\BACKUP_SIA",
        "disco_externo":  r"E:\BACKUP_SIA",
        "archivos_clave": [
            "dashboard_sia_v5_3_FINAL.py",
            "sap_match_engine_robusto.py",
            "procesar_con_joins_COMPLETO.py",
        ]
    },
    "ELPASAJE": {
        "repo_path":      r"C:\Trabajo\ElPasaje",
        "branch":         "main",
        "google_drive":   r"C:\Users\ar028883\Google Drive\BACKUP_ELPASAJE",
        "disco_externo":  r"E:\BACKUP_ELPASAJE",
        "archivos_clave": [
            "app.py",
            "requirements.txt",
        ]
    }
}

LOG_PATH = Path.home() / "backup_manager_log.json"

# ══════════════════════════════════════════════════════
# FUNCIONES CORE
# ══════════════════════════════════════════════════════

def _timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _fecha_archivo():
    return datetime.now().strftime("%Y%m%d_%H%M")

def _log(proyecto, resultado, detalle=""):
    """Guarda un registro de cada backup en un archivo JSON."""
    entrada = {
        "timestamp": _timestamp(),
        "proyecto": proyecto,
        "resultado": resultado,
        "detalle": detalle
    }
    logs = []
    if LOG_PATH.exists():
        try:
            logs = json.loads(LOG_PATH.read_text(encoding="utf-8"))
        except:
            logs = []
    logs.append(entrada)
    # Conserva solo los últimos 200 registros
    logs = logs[-200:]
    LOG_PATH.write_text(json.dumps(logs, ensure_ascii=False, indent=2), encoding="utf-8")

def _git_backup(repo_path, branch, motivo):
    """
    Hace add + commit + push al repo de GitHub.
    Retorna (True, mensaje) o (False, error).
    """
    try:
        os.chdir(repo_path)
        
        # Verificar si hay cambios
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True
        )
        
        if not status.stdout.strip():
            return True, "Sin cambios nuevos — nada que commitear"
        
        # Add
        subprocess.run(["git", "add", "."], check=True)
        
        # Commit con timestamp
        msg = f"[AUTO] {motivo} — {_timestamp()}"
        subprocess.run(["git", "commit", "-m", msg], check=True)
        
        # Push
        subprocess.run(["git", "push", "origin", branch], check=True)
        
        return True, f"Commit: {msg}"
    
    except subprocess.CalledProcessError as e:
        return False, f"Error git: {e}"
    except Exception as e:
        return False, f"Error inesperado: {e}"

def _copiar_a_destino(repo_path, destino_base, archivos_clave):
    """
    Copia los archivos clave a la carpeta de destino (Google Drive o disco externo).
    Crea subcarpeta con fecha para tener historial.
    """
    try:
        destino = Path(destino_base) / _fecha_archivo()
        destino.mkdir(parents=True, exist_ok=True)
        
        copiados = []
        for archivo in archivos_clave:
            origen = Path(repo_path) / archivo
            if origen.exists():
                shutil.copy2(origen, destino / archivo)
                copiados.append(archivo)
        
        # También copia el .env si existe (sin subir a GitHub)
        env_file = Path(repo_path) / ".env"
        if env_file.exists():
            shutil.copy2(env_file, destino / ".env")
            copiados.append(".env")
        
        return True, f"Copiados {len(copiados)} archivos → {destino}"
    
    except Exception as e:
        return False, f"Error al copiar: {e}"

def _ejecutar_backup(proyecto_key, motivo="Backup manual"):
    """Ejecuta el backup completo para un proyecto."""
    cfg = CONFIG[proyecto_key]
    nombre = proyecto_key
    resultados = []
    
    print(f"\n{'='*55}")
    print(f"  BACKUP {nombre} — {_timestamp()}")
    print(f"  Motivo: {motivo}")
    print(f"{'='*55}")
    
    # 1. GitHub
    print("\n📤 GitHub...")
    ok, msg = _git_backup(cfg["repo_path"], cfg["branch"], motivo)
    estado = "✅" if ok else "❌"
    print(f"   {estado} {msg}")
    resultados.append(("GitHub", ok, msg))
    
    # 2. Google Drive
    print("\n☁️  Google Drive...")
    gd_path = cfg["google_drive"]
    # Detectar si Google Drive usa otra ruta
    rutas_gdrive = [
        gd_path,
        gd_path.replace("Google Drive", "My Drive"),
        gd_path.replace("Google Drive", "GoogleDrive"),
    ]
    gd_encontrado = next((r for r in rutas_gdrive if Path(r.rsplit("\\",1)[0]).exists()), None)
    
    if gd_encontrado:
        ok, msg = _copiar_a_destino(cfg["repo_path"], gd_encontrado, cfg["archivos_clave"])
        estado = "✅" if ok else "❌"
        print(f"   {estado} {msg}")
        resultados.append(("Google Drive", ok, msg))
    else:
        print(f"   ⚠️  Google Drive no encontrado en esta PC — omitido")
        resultados.append(("Google Drive", False, "Carpeta no encontrada"))
    
    # 3. Disco Externo
    print("\n💾 Disco externo...")
    disco = cfg["disco_externo"]
    disco_letra = disco[0] + ":\\"
    if Path(disco_letra).exists():
        ok, msg = _copiar_a_destino(cfg["repo_path"], disco, cfg["archivos_clave"])
        estado = "✅" if ok else "❌"
        print(f"   {estado} {msg}")
        resultados.append(("Disco externo", ok, msg))
    else:
        print(f"   ⚠️  Disco externo no conectado — omitido (se activa cuando lo conectes)")
        resultados.append(("Disco externo", False, "No conectado"))
    
    # Resumen
    exitosos = sum(1 for _, ok, _ in resultados if ok)
    print(f"\n{'='*55}")
    print(f"  Resultado: {exitosos}/{len(resultados)} destinos OK")
    print(f"{'='*55}\n")
    
    # Log
    detalle = " | ".join([f"{d}: {'OK' if ok else 'FAIL'}" for d, ok, _ in resultados])
    _log(nombre, "OK" if exitosos > 0 else "FAIL", detalle)
    
    return exitosos > 0

# ══════════════════════════════════════════════════════
# FUNCIONES PÚBLICAS — para importar desde otros scripts
# ══════════════════════════════════════════════════════

def backup_sia(motivo="Ejecucion automatica SIA"):
    """Llamar esto al final de sap_match_engine."""
    return _ejecutar_backup("SIA", motivo)

def backup_elpasaje(motivo="Ejecucion automatica El Pasaje"):
    return _ejecutar_backup("ELPASAJE", motivo)

def backup_ambos(motivo="Backup manual ambos proyectos"):
    ok1 = _ejecutar_backup("SIA", motivo)
    ok2 = _ejecutar_backup("ELPASAJE", motivo)
    return ok1 and ok2

# ══════════════════════════════════════════════════════
# PROGRAMAR BACKUP DIARIO A LAS 20HS (Windows Task Scheduler)
# ══════════════════════════════════════════════════════

def programar_backup_diario():
    """
    Crea una tarea en el Programador de tareas de Windows
    para ejecutar el backup de El Pasaje todos los días a las 20hs.
    """
    python_exe = sys.executable
    script = str(Path(__file__).resolve())
    
    cmd = [
        "schtasks", "/create", "/f",
        "/tn", "BackupElPasajeDiario",
        "/tr", f'"{python_exe}" "{script}" elpasaje',
        "/sc", "daily",
        "/st", "20:00",
        "/ru", os.environ.get("USERNAME", ""),
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("✅ Tarea programada: backup El Pasaje todos los días a las 20:00hs")
        print("   Podés verla en: Programador de tareas → BackupElPasajeDiario")
    except Exception as e:
        print(f"❌ Error al programar: {e}")
        print("   Intentá correr el CMD como Administrador")

# ══════════════════════════════════════════════════════
# MAIN — ejecución desde terminal
# ══════════════════════════════════════════════════════

if __name__ == "__main__":
    arg = sys.argv[1].lower() if len(sys.argv) > 1 else "ayuda"
    
    if arg == "sia":
        backup_sia("Backup manual SIA")
    elif arg in ("elpasaje", "pasaje"):
        backup_elpasaje("Backup manual El Pasaje")
    elif arg == "ambos":
        backup_ambos()
    elif arg == "programar":
        programar_backup_diario()
    elif arg == "log":
        if LOG_PATH.exists():
            logs = json.loads(LOG_PATH.read_text(encoding="utf-8"))
            for entry in logs[-10:]:
                print(f"{entry['timestamp']} | {entry['proyecto']} | {entry['resultado']} | {entry['detalle']}")
        else:
            print("Sin registros todavía.")
    else:
        print("""
USO:
  python backup_manager.py sia          → backup SIA ahora
  python backup_manager.py elpasaje     → backup El Pasaje ahora
  python backup_manager.py ambos        → backup los dos ahora
  python backup_manager.py programar    → activa backup diario 20hs (El Pasaje)
  python backup_manager.py log          → ver los últimos 10 backups
        """)
