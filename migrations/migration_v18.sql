-- migration_v18: re-aplicar fix de ODE-KIT-JAR (migration_v15 lo aplicó a medias)
--
-- Contexto (24/09/2026): migration_runner.py tenía un bug en el parseo de
-- statements — cuando un archivo .sql empieza con un bloque de comentarios,
-- el PRIMER statement queda pegado a ese bloque en el primer split por ";"
-- y el chunk entero se descarta por empezar con "--". Esto hizo que
-- migration_v15.sql (que arranca con comentario) solo aplicara su SEGUNDO
-- UPDATE (ODE-KIT-SUC) — el primero (ODE-KIT-JAR) nunca se ejecutó en Supabase,
-- aunque quedó registrada como "ejecutada" en schema_migrations porque no tiró
-- error. El bug de parseo se corrigió en utils/migration_runner.py (24/09).
-- migration_v15.sql NO se toca (append-only) — esta migration re-aplica
-- el UPDATE que faltó.
--
-- WHERE defensivo e idempotente: no hace nada si el dato ya es correcto.

UPDATE products
SET name  = 'Kit Jardinero Urbano',
    price = 12000
WHERE sku = 'ODE-KIT-JAR'
  AND (name != 'Kit Jardinero Urbano' OR price != 12000);
