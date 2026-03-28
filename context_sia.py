# -*- coding: utf-8 -*-
"""
CONTEXT SIA v2 — Lo que el agente sabe sobre SIA
Alejandra Gomez Aguilera

ACTUALIZACIÓN v2:
  Incorpora lógica real de gestor_errores_log.py y scoring_proveedores.py:
  - Directorio de emails por centro
  - Procedimiento de resolución (IW32, SIA-APROV-001)
  - Sistema de scoring con pesos y penalizaciones
  - Clasificación A-E de proveedores
"""

import os
from datetime import datetime

try:
    import pandas as pd
    PANDAS_OK = True
except ImportError:
    PANDAS_OK = False

NOMBRE = "Agente SIA"

RUTAS = {
    "errores": r"C:\Users\ar028883\Documents\SIA_Project\reportes\analisis\ERRORES_DETECTADOS.xlsx",
    "scoring": r"C:\Users\ar028883\Documents\SIA_Project\reportes\scoring\RANKING_PROVEEDORES.xlsx",
}

SYSTEM_PROMPT = """
Sos el Agente SIA de Alejandra Gomez Aguilera en Control de Gestión - Orden de Vuelo de Aerolíneas Argentinas.
Tu rol: analizar errores en Órdenes de Vuelo y dar instrucciones concretas de resolución incluyendo a quién contactar.

═══════════════════════════════════════════════
LOS 10 TIPOS DE ERROR — CON PROCEDIMIENTO
═══════════════════════════════════════════════
1. SIN_CONTRATO (CRÍTICO | -10 pts)
   Resolver: cargar número de contrato en SAP (IW32) | Área: Compras | Proc: SIA-APROV-001

2. REMITO_INVALIDO (MEDIA | -2 pts)
   Resolver: corregir número de remito con el proveedor (debe ser 12 dígitos)
   Gate Gourmet falla los LUNES en 1EZE con 11 dígitos

3. FACTURA_SIN_OV (CRÍTICO)
   Resolver: vincular factura a la OV correspondiente | Área: Contabilidad

4. ELLS_LIMITE (CRÍTICO | -5 pts)
   Resolver: gestionar ampliación de contrato antes del vencimiento | Área: Compras + Control de Gestión

5. ESTADO_INVALIDO (BAJA)
   Resolver: corregir status en IW32 | Área: Escala

6. PUESTO_INVALIDO (BAJA | -10 pts)
   Resolver: reasignar al puesto correcto | Área: Escala

7. VUELO_CANCELADO (MEDIA)
   Resolver: verificar reprogramación o anular operación | Área: Operaciones + Aprovisionamiento

8. CANTIDAD_INCONSISTENTE (MEDIA)
   Resolver: reconciliar cantidades con el proveedor | Área: Aprovisionamiento

9. PROVEEDOR_SIN_ALTA (BAJA | -7 pts)
   Resolver: dar de alta en FK01 | Área: Compras

10. SERVICIO_NO_DETERMINADO (BAJA)
    Resolver: actualizar tabla zds_deter | Área: Control de Gestión

═══════════════════════════════════════════════
DIRECTORIO DE ESCALAS
═══════════════════════════════════════════════
1AEP Aeroparque:  escala.aeroparque@aerolineas.com.ar
1EZE Ezeiza:      escala.ezeiza@aerolineas.com.ar
1COR Córdoba:     escala.cordoba@aerolineas.com.ar
1MDZ Mendoza:     escala.mendoza@aerolineas.com.ar
1USH Ushuaia:     escala.ushuaia@aerolineas.com.ar
1BRC Bariloche:   escala.bariloche@aerolineas.com.ar
1IGR Iguazú:      escala.iguazu@aerolineas.com.ar
1SAL Salta:       escala.salta@aerolineas.com.ar
1TUC Tucumán:     escala.tucuman@aerolineas.com.ar
1ROS Rosario:     escala.rosario@aerolineas.com.ar
Otros:            escalas.general@aerolineas.com.ar

═══════════════════════════════════════════════
SCORING DE PROVEEDORES (0-100)
═══════════════════════════════════════════════
Pesos: error 35% | resolución 25% | contratos 15% | volumen 10% | sobrecostos 15%
Clasificación: A≥80 | B≥65 | C≥50 | D≥35 | E<35
Penalizaciones: SIN_CONTRATO -10 | PUESTO_INVALIDO -10 | CONTRATO_VENCIDO -8 | PROVEEDOR_SIN_ALTA -7 | ELLS_LIMITE -5 | REVI_VENCIDO -3 | REMITO_INVALIDO -2

═══════════════════════════════════════════════
PROVEEDORES PRINCIPALES
═══════════════════════════════════════════════
Gate Gourmet Argentina S.R.L.: catering principal. REMITO_INVALIDO lunes en 1EZE.
LSG Sky Chefs: catering secundario. FACTURA_SIN_OV histórico.
Dnata: handling. ELLS_LIMITE frecuente.

═══════════════════════════════════════════════
PATRONES TEMPORALES
═══════════════════════════════════════════════
Lunes: mayor volumen → REMITO_INVALIDO Gate Gourmet 1EZE
Fin de mes: picos facturación → SIN_CONTRATO
Principios de año: cambios contratos → SIN_CONTRATO masivos
Vuelos cancelados → cascada de FACTURA_SIN_OV

═══════════════════════════════════════════════
COMPORTAMIENTO
═══════════════════════════════════════════════
- Español, técnico, directo
- Para cada error: tipo + área + email de escala + procedimiento
- Ordenar por impacto financiero (campo Impacto_Financiero)
- Señalar patrones recurrentes
- Marcar anomalías de volumen según día de semana
- Incluir clasificación A-E del proveedor cuando esté disponible
"""


def get_data_context() -> str:
    hoy = datetime.now().strftime("%d/%m/%Y %H:%M")
    dia = datetime.now().strftime("%A")

    if not PANDAS_OK:
        return f"\n[SIA — {hoy}]\nInstalar: pip install pandas openpyxl\n"

    partes = [f"\n═══════════════════════════════════════════════\nDATOS SIA — {hoy} ({dia})\n═══════════════════════════════════════════════\n"]

    # Errores
    if os.path.exists(RUTAS["errores"]):
        try:
            df = pd.read_excel(RUTAS["errores"])
            partes.append(_errores(df))
        except Exception as e:
            partes.append(f"Error leyendo errores: {e}\n")
    else:
        partes.append("ERRORES_DETECTADOS.xlsx no encontrado — correr sap_match_engine_robusto.py primero\n")

    # Scoring
    if os.path.exists(RUTAS["scoring"]):
        try:
            df_sc = pd.read_excel(RUTAS["scoring"])
            partes.append(_scoring(df_sc))
        except:
            pass

    # Advertencia día
    partes.append(_dia(dia))
    return "\n".join(partes)


def _errores(df):
    if df.empty:
        return "ERRORES: ninguno ✅\n"
    lines = [f"ERRORES DETECTADOS: {len(df)}\n"]

    if 'Tipo_Error' in df.columns:
        lines.append("POR TIPO:")
        for t, n in df['Tipo_Error'].value_counts().items():
            e = "🔴" if t in {"SIN_CONTRATO","ELLS_LIMITE","FACTURA_SIN_OV"} else "🟡" if t in {"REMITO_INVALIDO","CANTIDAD_INCONSISTENTE","VUELO_CANCELADO"} else "⚪"
            lines.append(f"  {e} {t}: {n}")

    emails = {'1AEP':'escala.aeroparque@aerolineas.com.ar','1EZE':'escala.ezeiza@aerolineas.com.ar',
              '1COR':'escala.cordoba@aerolineas.com.ar','1MDZ':'escala.mendoza@aerolineas.com.ar',
              '1USH':'escala.ushuaia@aerolineas.com.ar'}

    if 'Centro' in df.columns:
        lines.append("\nPOR CENTRO:")
        for c, n in df['Centro'].value_counts().head(8).items():
            em = emails.get(str(c), 'escalas.general@aerolineas.com.ar')
            lines.append(f"  {c}: {n} → {em}")

    if 'Impacto_Financiero' in df.columns:
        lines.append(f"\nIMPACTO FINANCIERO TOTAL: ${df['Impacto_Financiero'].sum():,.2f} ARS")

    return "\n".join(lines) + "\n"


def _scoring(df):
    if df.empty or 'Score_Final' not in df.columns:
        return ""
    lines = ["\nSCORING PROVEEDORES:"]
    if 'Clasificacion' in df.columns:
        for cat, n in df['Clasificacion'].value_counts().sort_index().items():
            lines.append(f"  {cat}: {n}")
    lines.append("Top 3:")
    for _, r in df.head(3).iterrows():
        lines.append(f"  {r.get('Ranking','?')}. {str(r['Proveedor'])[:28]} {r['Score_Final']}/100 ({r.get('Clasificacion','')})")
    return "\n".join(lines) + "\n"


def _dia(dia):
    msgs = {
        "Monday": "⚠️  LUNES — revisar Gate Gourmet 1EZE por REMITO_INVALIDO.",
        "lunes":  "⚠️  LUNES — revisar Gate Gourmet 1EZE por REMITO_INVALIDO.",
        "Friday": "ℹ️  VIERNES — resolver todos los CRÍTICOS antes del fin de semana.",
        "viernes":"ℹ️  VIERNES — resolver todos los CRÍTICOS antes del fin de semana.",
    }
    msg = msgs.get(dia, "")
    return f"\nCONTEXTO: {msg}\n" if msg else ""

# ── Agregar rutas de alertas al dict
RUTAS["alertas_proveedores"] = r"C:\Users\ar028883\Documents\SIA_Project\reportes\alertas\PROVEEDORES_EN_DETERIORO.xlsx"
RUTAS["alertas_escalas"]     = r"C:\Users\ar028883\Documents\SIA_Project\reportes\alertas\ESCALAS_EN_DETERIORO.xlsx"
RUTAS["proyeccion"]          = r"C:\Users\ar028883\Documents\SIA_Project\reportes\alertas\PROYECCION_CIERRE_MENSUAL.xlsx"

# Patch get_data_context to also read alertas
_original_get_data_context = get_data_context

def get_data_context() -> str:
    base = _original_get_data_context()
    extras = []

    if PANDAS_OK:
        # Proveedores en deterioro
        if os.path.exists(RUTAS["alertas_proveedores"]):
            try:
                df = pd.read_excel(RUTAS["alertas_proveedores"])
                if not df.empty:
                    extras.append(f"\n⚠️  PROVEEDORES EN DETERIORO: {len(df)}")
                    for _, r in df.head(3).iterrows():
                        extras.append(f"  {r.get('Proveedor','?')[:28]} — tasa actual {r.get('Tasa_Actual','?')}% vs promedio {r.get('Tasa_Promedio','?'):.1f}% (+{r.get('Incremento_%','?')}%)")
            except:
                pass

        # Escalas en deterioro
        if os.path.exists(RUTAS["alertas_escalas"]):
            try:
                df = pd.read_excel(RUTAS["alertas_escalas"])
                if not df.empty:
                    extras.append(f"\n⚠️  ESCALAS EN DETERIORO: {len(df)}")
                    for _, r in df.head(3).iterrows():
                        extras.append(f"  {r.get('Escala','?')} — {r.get('Tasa_Error_Actual','?')}% vs {r.get('Tasa_Error_Anterior','?')}% mes anterior")
            except:
                pass

        # Proyección mensual
        if os.path.exists(RUTAS["proyeccion"]):
            try:
                df = pd.read_excel(RUTAS["proyeccion"])
                if not df.empty:
                    r = df.iloc[0]
                    extras.append(f"\nPROYECCIÓN CIERRE MENSUAL ({r.get('Mes','')}):")
                    extras.append(f"  Ops hasta hoy: {r.get('Ops_Hasta_Hoy','?'):,} | Proyectadas: {r.get('Ops_Proyectadas_Mes','?'):,}")
                    extras.append(f"  En REVI: {r.get('En_REVI_Hoy','?')} | Tasa cierre FINL: {r.get('Tasa_Cierre_%','?')}%")
            except:
                pass

    return base + "\n".join(extras)
