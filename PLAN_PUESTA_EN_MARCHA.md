# Plan de puesta en marcha — El Pasaje App

## Estado actual (hasta donde llegaron)

- Hay una app base en Streamlit (`elpasaje_v1.py`) con:
  - Login por perfiles (Admin, Familias, B2B, Invitado).
  - Base SQLite inicial con clientes y productos de ejemplo.
  - Dashboard y catálogo visual inicial.
  - Módulos de Inventario / Gestión / Proyectos STL ya operativos en versión v1.
- Dependencias mínimas definidas en `requirements.txt`.
- Repositorio sin documentación operativa para despliegue/QA.

## Objetivo de cierre de esta etapa

Dejar el proyecto **listo para operación controlada (MVP funcional)** con:
1. Flujo estable de autenticación y catálogo.
2. Módulos pendientes operativos en versión mínima usable.
3. Validaciones automáticas básicas.
4. Proceso de despliegue y respaldo documentado.

## Plan por fases

## Fase 1 — Estabilización técnica (1–2 días)

1. **Hardening inicial**
   - Mover credenciales hardcodeadas a variables de entorno.
   - Agregar control básico de errores de DB.
   - Evitar queries con interpolación directa cuando usen variables de usuario.

2. **Estructura de datos**
   - Crear migración inicial/versionado simple de esquema.
   - Agregar tablas mínimas para: `pedidos`, `movimientos_stock`, `proyectos_stl`.

3. **Observabilidad mínima**
   - Logging básico de login, altas/ediciones de producto y cambios de stock.

**Criterio de salida Fase 1:** app arranca en limpio, login estable, DB consistente y sin credenciales expuestas.

## Fase 2 — Completar módulos pendientes (2–4 días)

1. **Inventario**
   - ABM de productos (crear, editar, desactivar).
   - Ajustes de stock con motivo + historial.

2. **Gestión**
   - Vista de clientes por tipo (Familia/B2B).
   - Alta y edición básica de usuarios no-admin.

3. **Proyectos STL**
   - Registro de proyectos con estado (`nuevo`, `en_revision`, `en_produccion`, `entregado`).
   - Carga de metadatos (cliente, prioridad, fecha compromiso, notas).

**Criterio de salida Fase 2:** los tres módulos ya no muestran "en desarrollo" y soportan operación real básica.

## Fase 3 — Calidad y despliegue (1–2 días)

1. **Testing mínimo obligatorio**
   - Smoke test de arranque.
   - Pruebas de login por rol.
   - Pruebas de CRUD de inventario.

2. **Preparación de entorno**
   - Archivo `.env.example` con variables requeridas.
   - Script de inicialización de base y datos demo.

3. **Go-live controlado**
   - Checklist de release.
   - Respaldo diario de SQLite.
   - Definición de responsable operativo y ventana de soporte.

**Criterio de salida Fase 3:** versión desplegable con checklist y pruebas mínimas pasando.

## Backlog recomendado (post MVP)

- Roles y permisos granulares.
- Auditoría de acciones sensibles.
- API externa (FastAPI) + separación frontend/backend.
- Migración de SQLite a PostgreSQL para producción multiusuario.
- Reportería comercial (ventas, rotación de stock, margen por línea).

## Checklist de ejecución rápida (esta semana)

- [x] Cerrar seguridad básica (credenciales + queries + errores).
- [x] Implementar Inventario v1.
- [x] Implementar Gestión v1.
- [x] Implementar Proyectos STL v1.
- [x] Escribir pruebas mínimas y documentación de despliegue.
- [ ] Realizar salida a producción controlada.
