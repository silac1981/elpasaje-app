-- migration_v19: re-aplicar 2 statements de migration_v16 que el bug de
-- parseo de migration_runner.py descartó silenciosamente
--
-- Contexto (24/09/2026): mismo bug que migration_v18 (ver ese archivo para el
-- detalle) — migration_v16.sql también empieza con un bloque de comentarios,
-- y además tiene un segundo bloque de comentarios de sección ("PRODUCTOS")
-- pegado directo antes de un INSERT sin statement previo en el medio. Los dos
-- statements que quedaron fusionados con un comentario y por lo tanto nunca
-- se ejecutaron en Supabase:
--   1. INSERT del material 'petg_gris' (nunca se insertó/actualizó)
--   2. INSERT del producto 'M19-FDE-S' (Fidget de escritorio — nunca se dio de alta)
-- migration_v16.sql NO se toca (append-only). Ambos statements son
-- idempotentes por su propio ON CONFLICT, se re-aplican tal cual estaban.

INSERT INTO materials (material_id, name, tipo, color, proveedor, stock_gr, cost_kg, stock_minimo_gr, fecha_compra, precio_compra, activo) VALUES ('petg_gris', 'PETG Gris', 'PETG', 'Gris', 'MakerPanda', 25000.0, 19920.0, 2000, '2026-05-20', 19920.0, 1) ON CONFLICT (material_id) DO UPDATE SET name=EXCLUDED.name, stock_gr=EXCLUDED.stock_gr, cost_kg=EXCLUDED.cost_kg, stock_minimo_gr=EXCLUDED.stock_minimo_gr, precio_compra=EXCLUDED.precio_compra, activo=EXCLUDED.activo;

INSERT INTO products (sku, client_id, material_id, name, description, categoria, color, price, weight_gr, tiempo_impresion_min, stock, imagen_url, fecha_alta, activo, tipo_producto, visibilidad, proveedor_ref, precio_reventa, precio_socio) VALUES ('M19-FDE-S', 'admin', NULL, 'Fidget de escritorio — Botones', 'Botones táctiles de diferentes resistencias. Anclaje para el hiperfoco. Respaldo Aldana.', 'Fidgets', NULL, 8500.0, 45.0, 0, 0, NULL, '2026-05-20', 1, 'propio_3d', 'publico', NULL, 0.0, 0.0) ON CONFLICT (sku) DO NOTHING;
