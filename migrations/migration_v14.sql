-- migration_v14: Cambiar visibilidad OE-* (vkhome_cliente) de 'publico' a 'socio'
--
-- Contexto: Los productos OE-* tienen client_id='vkhome_cliente' (línea de Agustina).
-- Estaban marcados visibilidad='publico' pero PAGINAS_SOCIOS["vkhome_cliente"] = None
-- (sin página HTML pública). Agustina los gestiona desde su panel multi-línea.
-- → deben ser 'socio', no 'publico', para no aparecer en exports del catálogo público.
--
-- Ejecución: MANUAL vía SQL Editor del dashboard de Supabase (09/07/2026).
-- Causa: psycopg2 en timeout desde red local por incidente activo de Supabase
-- (status.supabase.com, "Project status change failures", última update 08/07 16:41 UTC).
-- Resultado confirmado: 9 filas actualizadas.

UPDATE products
SET visibilidad = 'socio'
WHERE client_id = 'vkhome_cliente'
  AND visibilidad = 'publico';
