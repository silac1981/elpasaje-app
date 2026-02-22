# QA Checklist MVP — El Pasaje

## 1) Smoke de arranque

1. Activar entorno virtual e instalar dependencias.
2. Ejecutar `streamlit run elpasaje_v1.py --server.port 8501`.
3. Confirmar que abre `http://localhost:8501` sin errores.

## 2) Login por rol

- Admin principal (`EP_ADMIN_USER` / `EP_ADMIN_PASSWORD`)
- Operaciones (`EP_OPS_USER` / `EP_OPS_PASSWORD`)
- Usuario FAMILIA (ej: `melomanos`)
- Usuario B2B (ej: `oasis`)
- Invitado (botón "Explorar Catálogo")

## 3) Inventario (flujo mínimo)

1. Alta de producto con foto local (`file_uploader`).
2. Validar que el producto aparece en la grilla.
3. Ajuste de stock positivo y negativo.
4. Verificar que no permite stock final negativo.
5. Verificar histórico en `Últimos movimientos`.

## 4) Gestión

1. Alta de cliente FAMILIA.
2. Alta de cliente B2B.
3. Verificar filtro por tipo (`TODOS`, `FAMILIA`, `B2B`).

## 5) Proyectos STL

1. Alta de proyecto para un cliente existente.
2. Cambiar estado (`nuevo`, `en_revision`, `en_produccion`, `entregado`).
3. Verificar actualización en grilla.

## 6) Catálogo

1. Verificar que las imágenes locales cargadas se muestren en catálogo.
2. Verificar fallback de imagen remota cuando no existe archivo local.

## 7) Evidencia mínima de cierre

- Captura de login y dashboard.
- Captura de alta de producto con foto.
- Captura de ajuste de stock.
- Captura de alta + cambio de estado de proyecto.
- Copia del archivo de logs: `logs/elpasaje.log`.
