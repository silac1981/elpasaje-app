"""
╔══════════════════════════════════════════════════════════════════╗
║          AGENTE MACRO — LOG MAESTRO                              ║
║          log_maestro.py                                          ║
║                                                                  ║
║  Base de datos unificada para SIA + El Pasaje (y cualquier       ║
║  sistema futuro). Esta es la infraestructura de ML:              ║
║  hoy registra → mañana aprende → pasado decide.                  ║
║                                                                  ║
║  ARQUITECTURA:                                                    ║
║    SIA          ──┐                                              ║
║    El Pasaje    ──┼──► log_maestro.db ──► Agente Macro           ║
║    Aviation Pro ──┘   (historia clínica    (ML en el futuro)     ║
║    [futuro]           unificada)                                 ║
╚══════════════════════════════════════════════════════════════════╝

FILOSOFÍA DE DISEÑO:
  - Un solo esquema para todos los sistemas
  - contexto_json: flexibilidad para eventos distintos
  - etiqueta_ml: vacío hoy, clave del ML mañana
  - resultado: convierte logs en entrenamiento supervisado

CÓMO USAR:
  from log_maestro import LogMaestro
  log = LogMaestro()
  log.registrar(sistema="SIA", tipo_evento="error_detectado", ...)
"""

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# ══════════════════════════════════════════════════════
# CONFIGURACIÓN DE RUTAS
# ══════════════════════════════════════════════════════

# La base vive junto al ep_pasaje.db para que el agente
# tenga todo en el mismo lugar.
RUTA_DB = Path(r"C:\Users\ar028883\Documents\elpasaje-app-clean\log_maestro.db")

# Sistemas válidos — si agregás uno nuevo, lo añadís acá.
SISTEMAS_VALIDOS = {"SIA", "ElPasaje", "AviationPro", "AgenteMacro"}

# Tipos de evento — vocabulario controlado para que el ML
# pueda aprender patrones entre sistemas.
TIPOS_EVENTO = {
    # SIA
    "error_detectado",      # SIA detectó un error en OV
    "error_resuelto",       # el error fue corregido
    "alerta_ells",          # servicio próximo al límite 9M de SAP
    "patron_proveedor",     # comportamiento anómalo de proveedor
    # El Pasaje
    "odv_creada",           # nueva orden de venta
    "odv_entregada",        # ODV completada
    "cliente_recurrente",   # cliente que vuelve a comprar
    "alerta_entrega",       # entrega próxima sin producción lista
    "patron_margen",        # producto con margen destacado
    "patron_demanda",       # categoría con mayor demanda
    # Agente Macro
    "patron_detectado",     # el agente encontró algo sin que vos lo definieras
    "prediccion",           # el agente predijo algo (Fase 3)
    "decision_sugerida",    # el agente sugirió una acción (Fase 4)
    "decision_ejecutada",   # la acción fue ejecutada
}

SEVERIDADES = {"critica", "alta", "media", "baja", "info"}

# ══════════════════════════════════════════════════════
# CLASE PRINCIPAL
# ══════════════════════════════════════════════════════

class LogMaestro:
    """
    Interfaz unificada para registrar eventos de cualquier sistema.
    
    PRINCIPIO CLAVE:
    El esquema tiene campos fijos (para consultas rápidas y ML)
    y un campo flexible contexto_json (para el detalle específico
    de cada sistema). Esto permite que SIA guarde 'tipo_error SAP'
    y El Pasaje guarde 'marca_ep' sin romper el esquema común.
    """

    def __init__(self, ruta_db: Path = RUTA_DB):
        self.ruta_db = ruta_db
        self._inicializar_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.ruta_db)
        conn.row_factory = sqlite3.Row
        return conn

    def _inicializar_db(self):
        """
        Crea las tablas si no existen.
        La tabla log_eventos es el corazón del sistema.
        Las tablas de metadatos guardan el contexto de los sistemas.
        """
        conn = self._get_conn()
        conn.executescript("""

        -- ══════════════════════════════════════════════
        -- TABLA PRINCIPAL: cada fila es un evento
        -- ══════════════════════════════════════════════
        CREATE TABLE IF NOT EXISTS log_eventos (

            id              INTEGER PRIMARY KEY AUTOINCREMENT,

            -- CUÁNDO
            timestamp       TEXT NOT NULL,   -- ISO 8601: '2025-06-15T20:00:00'
            fecha           TEXT NOT NULL,   -- '2025-06-15' (para GROUP BY fecha)
            hora            TEXT NOT NULL,   -- '20:00' (para detectar patrones temporales)

            -- QUÉ SISTEMA
            sistema         TEXT NOT NULL,   -- 'SIA' | 'ElPasaje' | 'AviationPro'
            version_sistema TEXT,            -- '5.3' | '2.2' (para rastrear evolución)

            -- QUÉ PASÓ
            tipo_evento     TEXT NOT NULL,   -- vocabulario controlado (TIPOS_EVENTO)
            severidad       TEXT DEFAULT 'info',  -- 'critica' | 'alta' | 'media' | 'baja' | 'info'
            descripcion     TEXT,            -- texto libre, legible por humanos

            -- SOBRE QUÉ ENTIDAD
            entidad_tipo    TEXT,            -- 'proveedor' | 'cliente' | 'producto' | 'marca'
            entidad_id      TEXT,            -- el ID o código de la entidad
            entidad_nombre  TEXT,            -- nombre legible

            -- VALOR NUMÉRICO PRINCIPAL (para ML numérico)
            valor_num       REAL,            -- importe, margen%, días, cantidad
            valor_unidad    TEXT,            -- 'ARS' | '%' | 'días' | 'unidades'

            -- DETALLE FLEXIBLE (para todo lo específico de cada sistema)
            contexto_json   TEXT,            -- JSON con los campos extra de cada sistema

            -- PARA ML — estos campos son el corazón del aprendizaje
            etiqueta_ml     TEXT,            -- NULL ahora → vos la ponés → el modelo la aprende
            confianza       REAL DEFAULT 0.7, -- 0 a 1: qué tan seguro está el sistema
            origen          TEXT DEFAULT 'regla',  -- 'regla' | 'modelo_ml' | 'manual'

            -- CIERRE DEL CICLO (sin esto no hay aprendizaje supervisado)
            resultado       TEXT,            -- NULL → 'resuelto' | 'ignorado' | 'error_repetido'
            resultado_fecha TEXT,            -- cuándo se cerró el ciclo
            confirmado_por  TEXT             -- 'alejandra' | 'agente' | 'automatico'
        );

        -- ══════════════════════════════════════════════
        -- ÍNDICES: sin estos, las consultas del agente
        -- serán lentas cuando tengas 100k+ eventos
        -- ══════════════════════════════════════════════
        CREATE INDEX IF NOT EXISTS idx_sistema   ON log_eventos(sistema);
        CREATE INDEX IF NOT EXISTS idx_fecha     ON log_eventos(fecha);
        CREATE INDEX IF NOT EXISTS idx_tipo      ON log_eventos(tipo_evento);
        CREATE INDEX IF NOT EXISTS idx_severidad ON log_eventos(severidad);
        CREATE INDEX IF NOT EXISTS idx_entidad   ON log_eventos(entidad_nombre);
        CREATE INDEX IF NOT EXISTS idx_etiqueta  ON log_eventos(etiqueta_ml);

        -- ══════════════════════════════════════════════
        -- TABLA DE SISTEMAS: metadatos de cada sistema
        -- registrado en el log
        -- ══════════════════════════════════════════════
        CREATE TABLE IF NOT EXISTS sistemas_registrados (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            sistema         TEXT UNIQUE NOT NULL,
            descripcion     TEXT,
            version_actual  TEXT,
            fecha_registro  TEXT,
            activo          INTEGER DEFAULT 1
        );

        -- ══════════════════════════════════════════════
        -- TABLA DE PATRONES: cuando el agente encuentra
        -- algo nuevo (no supervisado → semi-supervisado)
        -- ══════════════════════════════════════════════
        CREATE TABLE IF NOT EXISTS patrones_detectados (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp       TEXT NOT NULL,
            tipo_patron     TEXT,            -- 'cluster_proveedor' | 'anomalia_temporal' | etc.
            descripcion     TEXT,
            eventos_ids     TEXT,            -- JSON: lista de IDs del log que forman el patrón
            algoritmo       TEXT,            -- 'IsolationForest' | 'KMeans' | 'manual'
            confianza       REAL,
            etiqueta        TEXT,            -- vos la ponés después de revisar
            validado        INTEGER DEFAULT 0  -- 0=pendiente, 1=validado, -1=descartado
        );

        """)
        conn.commit()
        conn.close()

        # Registrar los sistemas conocidos
        self._registrar_sistema("SIA", "Sistema Inteligente Aerolíneas — detección errores OV", "5.3")
        self._registrar_sistema("ElPasaje", "El Pasaje 3D Studio — gestión ODV y catálogo", "2.2")
        self._registrar_sistema("AgenteMacro", "Agente coordinador inter-sistemas", "0.1")

    def _registrar_sistema(self, sistema: str, descripcion: str, version: str):
        conn = self._get_conn()
        conn.execute("""
            INSERT OR IGNORE INTO sistemas_registrados 
            (sistema, descripcion, version_actual, fecha_registro)
            VALUES (?, ?, ?, ?)
        """, (sistema, descripcion, version, datetime.now().isoformat()))
        conn.commit()
        conn.close()

    # ══════════════════════════════════════════════════
    # MÉTODO PRINCIPAL: registrar un evento
    # ══════════════════════════════════════════════════

    def registrar(
        self,
        sistema: str,
        tipo_evento: str,
        descripcion: str = "",
        severidad: str = "info",
        entidad_tipo: str = None,
        entidad_id: str = None,
        entidad_nombre: str = None,
        valor_num: float = None,
        valor_unidad: str = None,
        contexto: Dict[str, Any] = None,
        etiqueta_ml: str = None,
        confianza: float = 0.7,
        origen: str = "regla",
        version_sistema: str = None,
    ) -> int:
        """
        Registra un evento en el log maestro.
        
        Retorna el ID del evento creado.
        
        EJEMPLO DESDE SIA:
            log.registrar(
                sistema="SIA",
                tipo_evento="error_detectado",
                severidad="critica",
                entidad_tipo="proveedor",
                entidad_nombre="Gate Gourmet",
                descripcion="Remito con 11 dígitos en lugar de 12",
                valor_num=11,
                valor_unidad="dígitos",
                contexto={"orden": "4500123", "escala": "1EZE", "dia_semana": "lunes"},
                confianza=0.95,
            )
        
        EJEMPLO DESDE EL PASAJE:
            log.registrar(
                sistema="ElPasaje",
                tipo_evento="alerta_entrega",
                severidad="alta",
                entidad_tipo="cliente",
                entidad_nombre="Oasis Animal",
                descripcion="ODV EP-042 vence en 1 día, producción al 60%",
                valor_num=1,
                valor_unidad="días",
                contexto={"odv_id": "EP-042", "marca": "Magnitud19", "avance_pct": 60},
                confianza=1.0,
            )
        """
        now = datetime.now()
        
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO log_eventos (
                timestamp, fecha, hora,
                sistema, version_sistema,
                tipo_evento, severidad, descripcion,
                entidad_tipo, entidad_id, entidad_nombre,
                valor_num, valor_unidad,
                contexto_json,
                etiqueta_ml, confianza, origen
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            now.isoformat(),
            now.strftime("%Y-%m-%d"),
            now.strftime("%H:%M"),
            sistema,
            version_sistema,
            tipo_evento,
            severidad,
            descripcion,
            entidad_tipo,
            entidad_id,
            entidad_nombre,
            valor_num,
            valor_unidad,
            json.dumps(contexto or {}, ensure_ascii=False),
            etiqueta_ml,
            confianza,
            origen,
        ))
        evento_id = cur.lastrowid
        conn.commit()
        conn.close()
        return evento_id

    def cerrar_ciclo(self, evento_id: int, resultado: str, confirmado_por: str = "alejandra"):
        """
        ESTA ES LA FUNCIÓN MÁS IMPORTANTE PARA EL ML.
        
        Cuando sabés qué pasó con un evento, lo cerrás acá.
        Esos 'resultados' son los que van a entrenar el modelo supervisado.
        
        resultado puede ser:
          'resuelto'        → el error fue corregido
          'ignorado'        → se decidió no hacer nada
          'error_repetido'  → volvió a pasar
          'venta_cerrada'   → el cliente terminó comprando
          'venta_perdida'   → el cliente no compró
          'entrega_ok'      → la entrega llegó a tiempo
          'entrega_tarde'   → no llegó a tiempo
        """
        conn = self._get_conn()
        conn.execute("""
            UPDATE log_eventos
            SET resultado = ?, resultado_fecha = ?, confirmado_por = ?
            WHERE id = ?
        """, (resultado, datetime.now().isoformat(), confirmado_por, evento_id))
        conn.commit()
        conn.close()

    def etiquetar(self, evento_id: int, etiqueta: str):
        """
        Ponés una etiqueta ML a mano sobre un evento.
        Esto es el puente entre no supervisado y supervisado.
        
        Ejemplo: el agente detecta que Gate Gourmet falla los lunes.
        Vos lo revisás y le ponés etiqueta='falla_lunes_gate_gourmet'.
        En 6 meses el modelo detecta ese patrón solo.
        """
        conn = self._get_conn()
        conn.execute(
            "UPDATE log_eventos SET etiqueta_ml = ? WHERE id = ?",
            (etiqueta, evento_id)
        )
        conn.commit()
        conn.close()

    # ══════════════════════════════════════════════════
    # CONSULTAS — para el agente macro
    # ══════════════════════════════════════════════════

    def eventos_hoy(self, sistema: str = None) -> list:
        """Eventos del día, opcionalmente filtrados por sistema."""
        conn = self._get_conn()
        hoy = datetime.now().strftime("%Y-%m-%d")
        query = "SELECT * FROM log_eventos WHERE fecha = ?"
        params = [hoy]
        if sistema:
            query += " AND sistema = ?"
            params.append(sistema)
        query += " ORDER BY timestamp DESC"
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def eventos_sin_resultado(self, sistema: str = None) -> list:
        """
        Eventos que todavía no cerraron el ciclo.
        Esta lista es lo que el agente te muestra para que
        vayas completando los 'resultados' → alimentando el ML.
        """
        conn = self._get_conn()
        query = "SELECT * FROM log_eventos WHERE resultado IS NULL"
        params = []
        if sistema:
            query += " AND sistema = ?"
            params.append(sistema)
        query += " ORDER BY severidad DESC, timestamp DESC LIMIT 50"
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def resumen_para_email(self) -> dict:
        """
        Datos que el agente macro usa para el email unificado.
        Un solo resumen con ambos sistemas.
        """
        conn = self._get_conn()
        hoy = datetime.now().strftime("%Y-%m-%d")

        # Totales por sistema y severidad
        stats = conn.execute("""
            SELECT sistema, severidad, COUNT(*) as n
            FROM log_eventos
            WHERE fecha = ?
            GROUP BY sistema, severidad
            ORDER BY sistema, severidad
        """, (hoy,)).fetchall()

        # Eventos críticos del día (para mostrar primero)
        criticos = conn.execute("""
            SELECT sistema, tipo_evento, entidad_nombre, descripcion, confianza
            FROM log_eventos
            WHERE fecha = ? AND severidad IN ('critica', 'alta')
            ORDER BY confianza DESC
            LIMIT 10
        """, (hoy,)).fetchall()

        # Pendientes de cierre (sin resultado)
        pendientes = conn.execute("""
            SELECT sistema, COUNT(*) as n
            FROM log_eventos
            WHERE resultado IS NULL
            GROUP BY sistema
        """).fetchall()

        # Patrones detectados (no supervisado — Fase 2)
        patrones = conn.execute("""
            SELECT tipo_patron, descripcion, confianza, validado
            FROM patrones_detectados
            WHERE DATE(timestamp) = ?
            ORDER BY confianza DESC
        """, (hoy,)).fetchall()

        conn.close()
        return {
            "stats": [dict(r) for r in stats],
            "criticos": [dict(r) for r in criticos],
            "pendientes": [dict(r) for r in pendientes],
            "patrones": [dict(r) for r in patrones],
            "fecha": hoy,
        }

    def dataset_para_ml(self, sistema: str = None, solo_con_resultado: bool = True) -> list:
        """
        Exporta los eventos listos para entrenar un modelo.
        
        Solo usa esto en Fase 2-3 cuando tengas suficientes
        eventos CON resultado. Con pocos datos, el modelo aprende
        ruido en lugar de patrones.
        
        Regla práctica: necesitás mínimo 500 eventos con resultado
        para que valga la pena entrenar.
        """
        conn = self._get_conn()
        query = "SELECT * FROM log_eventos WHERE 1=1"
        params = []
        if sistema:
            query += " AND sistema = ?"
            params.append(sistema)
        if solo_con_resultado:
            query += " AND resultado IS NOT NULL"
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def stats_generales(self) -> dict:
        """Panel de salud del log maestro — cuántos datos tenés y qué tan útiles son para ML."""
        conn = self._get_conn()
        total = conn.execute("SELECT COUNT(*) FROM log_eventos").fetchone()[0]
        con_resultado = conn.execute(
            "SELECT COUNT(*) FROM log_eventos WHERE resultado IS NOT NULL"
        ).fetchone()[0]
        con_etiqueta = conn.execute(
            "SELECT COUNT(*) FROM log_eventos WHERE etiqueta_ml IS NOT NULL"
        ).fetchone()[0]
        por_sistema = conn.execute(
            "SELECT sistema, COUNT(*) as n FROM log_eventos GROUP BY sistema"
        ).fetchall()
        conn.close()

        pct_resultado = (con_resultado / total * 100) if total > 0 else 0
        pct_etiqueta  = (con_etiqueta  / total * 100) if total > 0 else 0

        return {
            "total_eventos": total,
            "con_resultado": con_resultado,
            "pct_resultado": round(pct_resultado, 1),
            "con_etiqueta":  con_etiqueta,
            "pct_etiqueta":  round(pct_etiqueta, 1),
            "por_sistema":   {r["sistema"]: r["n"] for r in por_sistema},
            "listo_para_ml": total >= 500 and pct_resultado >= 30,
            # ↑ Esto es un diagnóstico honesto: decirte si ya
            # tenés suficientes datos para entrenar un modelo.
        }


# ══════════════════════════════════════════════════════
# TEST RÁPIDO — corrés esto para verificar que funciona
# ══════════════════════════════════════════════════════

if __name__ == "__main__":
    import tempfile

    print("🧪 Testeando LogMaestro...\n")

    # Usar una DB temporal para el test
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        test_db = Path(f.name)

    log = LogMaestro(ruta_db=test_db)

    # Simular eventos de SIA
    id1 = log.registrar(
        sistema="SIA",
        tipo_evento="error_detectado",
        severidad="critica",
        entidad_tipo="proveedor",
        entidad_nombre="Gate Gourmet",
        descripcion="Remito con 11 dígitos en OV 4500123",
        valor_num=11,
        valor_unidad="dígitos",
        contexto={"orden": "4500123", "escala": "1EZE", "dia_semana": "lunes"},
        confianza=0.95,
    )
    print(f"✅ Evento SIA registrado (id={id1})")

    # Simular evento de El Pasaje
    id2 = log.registrar(
        sistema="ElPasaje",
        tipo_evento="alerta_entrega",
        severidad="alta",
        entidad_tipo="cliente",
        entidad_nombre="Oasis Animal",
        descripcion="ODV EP-042 vence en 1 día",
        valor_num=1,
        valor_unidad="días",
        contexto={"odv_id": "EP-042", "marca": "Magnitud19"},
        confianza=1.0,
    )
    print(f"✅ Evento El Pasaje registrado (id={id2})")

    # Cerrar el ciclo del primer evento (simular que se resolvió)
    log.cerrar_ciclo(id1, resultado="resuelto", confirmado_por="alejandra")
    print(f"✅ Ciclo cerrado para evento {id1}")

    # Ver stats
    stats = log.stats_generales()
    print(f"\n📊 Stats del log:")
    print(f"   Total eventos:    {stats['total_eventos']}")
    print(f"   Con resultado:    {stats['con_resultado']} ({stats['pct_resultado']}%)")
    print(f"   Listo para ML:    {stats['listo_para_ml']}")
    print(f"   Por sistema:      {stats['por_sistema']}")

    # Limpiar
    test_db.unlink()
    print(f"\n✅ Test completado — todo funciona correctamente.")
    print("\n" + "═"*55)
    print("  PRÓXIMO PASO:")
    print("  Integrar en ep_agente.py y en dashboard_sia_v5_3_FINAL.py")
    print("  con las funciones de integración (ver agente_macro.py)")
    print("═"*55)
