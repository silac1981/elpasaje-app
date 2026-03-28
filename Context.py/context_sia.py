# context_sia.py
import os
from datetime import datetime

NOMBRE = "Agente SIA"

SYSTEM_PROMPT = """Sos el Agente SIA de Alejandra en Control de Gestion Orden de Vuelo de Aerolineas Argentinas.
SIA detecta errores en Ordenes de Vuelo exportadas de SAP (transaccion ZR154).
10 tipos de error: SIN_CONTRATO, REMITO_INVALIDO, FACTURA_SIN_OV, ELLS_LIMITE, ESTADO_INVALIDO, PUESTO_INVALIDO, VUELO_CANCELADO, CANTIDAD_INCONSISTENTE, PROVEEDOR_SIN_ALTA, SERVICIO_NO_DETERMINADO.
Proveedor clave: Gate Gourmet falla con remitos de 11 digitos los lunes en escala 1EZE.
Criticos: SIN_CONTRATO, ELLS_LIMITE, FACTURA_SIN_OV. Los lunes hay mas errores por acumulacion del fin de semana.
Respondes en español, tecnico y directo."""

def get_data_context():
    hoy = datetime.now().strftime("%d/%m/%Y %H:%M")
    dia = datetime.now().strftime("%A")
    
    ruta = r"C:\Users\ar028883\Documents\SIA_Project\reportes\analisis\ERRORES_DETECTADOS.xlsx"
    
    if not os.path.exists(ruta):
        return f"[SIA al {hoy}]\nERRORES_DETECTADOS.xlsx no encontrado.\nCorrer sap_match_engine_robusto.py primero."
    
    try:
        import pandas as pd
        df = pd.read_excel(ruta)
        resumen = f"DATOS SIA AL {hoy} ({dia})\nTotal errores: {len(df)}\n"
        if 'Tipo_Error' in df.columns or 'tipo_error' in df.columns:
            col = 'Tipo_Error' if 'Tipo_Error' in df.columns else 'tipo_error'
            resumen += "POR TIPO:\n"
            for tipo, n in df[col].value_counts().head(10).items():
                resumen += f"  {tipo}: {n}\n"
        return resumen
    except Exception as e:
        return f"[Error leyendo SIA: {e}]"
