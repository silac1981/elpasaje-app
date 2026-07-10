-- migration_v15: Fix ODE-KIT-JAR y ODE-KIT-SUC en Supabase
--
-- Contexto: Los fixes de nombres y precios del Ciclo 2 (sesion 09/07/2026)
-- se aplicaron al SQLite local pero no a Supabase.
-- Esta migration sincroniza los valores correctos en Supabase.
-- WHERE defensivo e idempotente: no hace nada si los datos ya son correctos.

UPDATE products
SET name  = 'Kit Jardinero Urbano',
    price = 12000
WHERE sku = 'ODE-KIT-JAR'
  AND (name != 'Kit Jardinero Urbano' OR price != 12000);

UPDATE products
SET name  = 'Kit Suculentas',
    price = 18000
WHERE sku = 'ODE-KIT-SUC'
  AND (name != 'Kit Suculentas' OR price != 18000);
