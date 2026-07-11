"""
Fix mojibake en modules/panel_fer.py
Ejecutar desde C:\Trabajo\ElPasaje con: python _fix_panel_fer.py

El archivo tiene UTF-8 doble-codificado (fue editado con editor CP1252).
Fix: decode utf-8 -> encode cp1252 -> decode utf-8 para recuperar chars originales.
Tambien reemplaza GROUP_CONCAT -> STRING_AGG para PostgreSQL.
"""
import os

path = os.path.join(os.path.dirname(__file__), "modules", "panel_fer.py")

with open(path, 'rb') as f:
    raw = f.read()

# Decodificar como UTF-8 (da mojibake)
text = raw.decode('utf-8')

# Tabla de reemplazos mojibake -> correcto (CP1252 -> UTF-8)
# Derivados empiricamente del archivo:
FIXES = [
    # Dots, dashes, special
    ("Â·", "·"),
    ("â€"", "—"),
    ("â€™", "'"),
    ("â€œ", "“"),  # open quote
    ("â€\x9d", "”"),  # close quote
    # Emojis (UTF-8 doble codificado via CP1252)
    ("ðŸ–¨ï¸", "🖨️"),
    ("ðŸ§µ", "🧵"),
    ("ðŸ"‹", "📋"),
    ("ðŸ› ï¸", "🛠️"),
    ("ðŸ"¦", "📦"),
    ("ðŸ"", "📁"),
    ("ðŸ¤–", "🤖"),
    ("âœ…", "✅"),
    ("âš ï¸", "⚠️"),
    ("âŒ", "❌"),
    ("ðŸ†•", "🆕"),
    ("â³", "⏳"),
    # Spanish chars
    ("Ã³", "ó"),
    ("Ã­", "í"),
    ("Ã©", "é"),
    ("Ã¡", "á"),
    ("Ãº", "ú"),
    ("Ã±", "ñ"),
    ("Ã\x81", "Á"),
    ("Ã‰", "É"),
    ("Ã"", "Ó"),
    ("Ã", "Ó"),   # may vary
    # Other
    ("Ã—", "×"),
    ("MÃ­nimo", "Mínimo"),
    ("producciÃ³n", "producción"),
    ("fabricaciÃ³n", "fabricación"),
    ("mÃ¡s", "más"),
    ("PodÃ©s", "Podés"),
    ("pestaÃ±a", "pestaña"),
    ("Ãšltima", "Última"),
    ("versiÃ³n", "versión"),
    ("estÃ¡", "está"),
    ("dÃ­a", "día"),
    # GROUP_CONCAT -> STRING_AGG for PostgreSQL
    ("GROUP_CONCAT(DISTINCT client_id)", "STRING_AGG(DISTINCT client_id, ',')"),
]

fixed = text
for wrong, right in FIXES:
    fixed = fixed.replace(wrong, right)

# Backup del original
with open(path + '.bak', 'wb') as f:
    f.write(raw)

# Escribir el corregido
with open(path, 'w', encoding='utf-8') as f:
    f.write(fixed)

changes = sum(1 for (w, r) in FIXES if w in text)
print(f"OK: {changes}/{len(FIXES)} reemplazos aplicados en {path}")
print(f"Backup: {path}.bak")
