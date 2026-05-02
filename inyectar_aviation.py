"""
Script: inyectar_aviation.py
Ejecutar desde la carpeta del proyecto:
  python inyectar_aviation.py

Inserta / actualiza:
  - Tenant: Nando (Aviation Pro)
  - 13 productos iniciales de Aviation Pro
"""

import os
from sqlalchemy import create_engine, text

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "elpasaje_v2.db")
engine  = create_engine(f"sqlite:///{DB_PATH}")

with engine.connect() as conn:

    # ─────────────────────────────────────────────
    #  TENANT — Nando
    # ─────────────────────────────────────────────
    conn.execute(text("""
        INSERT INTO tenants (id, name, email, password)
        VALUES ('aviation', 'Fernando Gomez Aguilera (Nando)', 'aviation@elpasaje.com', '123')
        ON CONFLICT(id) DO UPDATE SET
            name     = excluded.name,
            email    = excluded.email,
            password = excluded.password
    """))
    print("✅ Tenant Aviation Pro — Nando creado/actualizado")

    # ─────────────────────────────────────────────
    #  PRODUCTOS
    # ─────────────────────────────────────────────
    productos = [
        # SKU               Nombre                          Peso(g)  Precio   Stock  Desc
        ("AVP-001", "Rampa-Safe",                            85,     4500,    5,  "Soporte celular/radio con base pesada y legajo en relieve. Ideal para vibraciones del hangar."),
        ("AVP-002", "Mate-Carro",                            70,     3800,    5,  "Accesorio para carro de herramientas personal. Sostiene mate y termo. Evita derrames."),
        ("AVP-003", "Clip Seguridad EPP",                    35,     2200,    8,  "Clip naranja de alta visibilidad para colgar protectores auditivos o guantes en el cinturon."),
        ("AVP-004", "Porta-Credencial Pro",                  45,     2800,    8,  "Funda rigida 3D personalizada con legajo. Protege tarjeta magnetica de roce y quimicos."),
        ("AVP-005", "Organizador Banco Personal",           120,     5500,    3,  "Bandeja modular para banco de trabajo personal: llaves, documentos y mate."),
        ("AVP-006", "Dock Checklist",                        75,     4200,    5,  "Soporte post-its y lapicera con forma de pista de aterrizaje. Lo urgente siempre a la vista."),
        ("AVP-007", "Organizador Fuselaje",                  60,     3500,    6,  "Sistema de clips con forma de remaches aeronauticos para cables en el borde del escritorio."),
        ("AVP-008", "Torre de Control",                     110,     5800,    3,  "Soporte auriculares Teams/Zoom inspirado en torres de control de EZE/AEP."),
        ("AVP-009", "Placa Analista Senior",                 90,     4800,    4,  "Placa de escritorio con nombre y legajo. Diseno inspirado en paneles de cabina de mando."),
        ("AVP-010", "Portabotella Aero",                     55,     3200,    6,  "Soporte para botella/termo de oficina con base antideslizante y logo grabado."),
        ("AVP-011", "Soporte Monitor Desk",                 180,     7500,    3,  "Elevador de monitor con bandeja inferior para teclado y mouse. Estetica aerolinea."),
        ("AVP-012", "Portacelular Escritorio 360",           65,     3800,    6,  "Porta celular articulado 360 grados para escritorio. Base pesada antideslizante."),
        ("AVP-013", "Hub Organizador USB",                   95,     4500,    4,  "Soporte organizador para hub USB y cables de carga. Mantiene el escritorio sin cables sueltos."),
    ]

    for sku, nombre, peso, precio, stock, desc in productos:
        conn.execute(text("""
            INSERT INTO products (client_id, name, sku, price, weight_gr, stock, description)
            VALUES ('aviation', :nombre, :sku, :precio, :peso, :stock, :desc)
            ON CONFLICT(sku) DO UPDATE SET
                name        = excluded.name,
                price       = excluded.price,
                weight_gr   = excluded.weight_gr,
                stock       = excluded.stock,
                description = excluded.description
        """), {"nombre": nombre, "sku": sku, "precio": precio,
               "peso": peso, "stock": stock, "desc": desc})
        print(f"   ✅ {sku} — {nombre}")

    conn.commit()

print("\n🚀 Aviation Pro cargada completa en el sistema.")
print("   Tenant : aviation@elpasaje.com / 123")
print("   Productos: 13 SKUs listos")
