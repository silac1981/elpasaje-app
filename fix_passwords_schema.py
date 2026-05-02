"""
fix_passwords_schema.py
========================
Reemplaza el bloque TENANTS_INICIALES en crear_schema_v3.py
con passwords ya hasheadas en SHA256.
Ejecutar UNA SOLA VEZ desde la carpeta del proyecto.
"""
import re

ARCHIVO = "crear_schema_v3.py"

# Hash SHA256 de cada password
# admin123 → 240be518...
# 123      → a665a459...
HASH_ADMIN = "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9"
HASH_123   = "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3"

TENANTS_NUEVO = f'''TENANTS_INICIALES = [
    ("admin",            "Alejandra",                         "admin@elpasaje.com",       "{HASH_ADMIN}",  None,          "admin",   "Direccion Economica", HOY, 1),
    ("olivia_coquette",  "Olivia",                            "coquette@elpasaje.com",    "{HASH_123}",    None,          "familia", None,                  HOY, 1),
    ("francisco_sport",  "Francisco",                         "fsport@elpasaje.com",      "{HASH_123}",    None,          "familia", None,                  HOY, 1),
    ("constantino_tech", "Constantino",                       "coretech@elpasaje.com",    "{HASH_123}",    None,          "familia", None,                  HOY, 1),
    ("aviation",         "Fernando Gomez Aguilera (Nando)",   "aviation@elpasaje.com",    "{HASH_123}",    None,          "b2b",     "Mantenimiento",       HOY, 1),
    ("oasis_animal",     "Oasis Animal",                      "oasisanimal@elpasaje.com", "{HASH_123}",    None,          "b2b",     None,                  HOY, 1),
    ("oasis_del_estero", "Oasis del Estero",                  "oasisestero@elpasaje.com", "{HASH_123}",    None,          "b2b",     None,                  HOY, 1),
    ("pharma_delux",     "Pharma DeLux",                      "pharma@elpasaje.com",      "{HASH_123}",    None,          "b2b",     None,                  HOY, 1),
]'''

with open(ARCHIVO, "r", encoding="utf-8") as f:
    contenido = f.read()

# Reemplazar el bloque TENANTS_INICIALES completo
nuevo = re.sub(
    r'TENANTS_INICIALES\s*=\s*\[.*?\]',
    TENANTS_NUEVO,
    contenido,
    flags=re.DOTALL
)

with open(ARCHIVO, "w", encoding="utf-8") as f:
    f.write(nuevo)

print("✅ crear_schema_v3.py actualizado con passwords hasheadas")
print()
print("Credenciales para usar en el login:")
print("  admin@elpasaje.com       → admin123")
print("  aviation@elpasaje.com    → 123")
print("  coretech@elpasaje.com    → 123")
print("  (todos los socios usan password: 123)")
print()
print("Próximo paso:")
print("  git add crear_schema_v3.py")
print('  git commit -m "fix: passwords hasheadas SHA256 en schema"')
print("  git push")
print()
print("Streamlit Cloud va a leer el schema actualizado")
print("y las credenciales van a funcionar desde el próximo deploy.")
