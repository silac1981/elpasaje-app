-- migration_v17: imagen_url para Oasis Animal (mapeo confirmado visualmente)
--
-- Contexto: fotos en static/productos/oasis-animal/ desde abril 2026, sin mapear
-- a SKUs en Supabase. Confirmado por inspeccion visual de las fotos en sesion
-- del 24/09/2026 (ver PROMPT_CLAUDECODE_EPCC_LOOP_MEJORA.md).
--
-- Solo se mapean acá los 2 casos sin ambigüedad. Quedan pendientes de
-- confirmación de Ale/Agustina: chapas_poncho.jpg (chapa personalizada
-- "Poncho", no está claro a qué SKU corresponde) y clip_dispensador_A/B.jpg
-- (dispensador de bolsitas — no existe SKU para este producto en el catálogo
-- actual). soporte_comedero_cruz.jpg es la pata/soporte del mismo producto
-- que soporte_comedero.jpg (mismo SKU OA-SCP-U), no un producto distinto.
--
-- WHERE defensivo e idempotente: no hace nada si los datos ya son correctos.

UPDATE products
SET imagen_url = 'static/productos/oasis-animal/perrito_globo_1.jpg'
WHERE sku = 'OA-LPG-U'
  AND (imagen_url IS NULL OR imagen_url != 'static/productos/oasis-animal/perrito_globo_1.jpg');

UPDATE products
SET imagen_url = 'static/productos/oasis-animal/soporte_comedero.jpg'
WHERE sku = 'OA-SCP-U'
  AND (imagen_url IS NULL OR imagen_url != 'static/productos/oasis-animal/soporte_comedero.jpg');
