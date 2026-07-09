"""migration_v13.py — Poblar whatsapp_numero en lineas_config.

Establece el número de WhatsApp por línea para que el sistema interno
y los exports HTML usen el número correcto de cada socio.

Números en formato 549 (internacional Argentina móvil para wa.me links).
Los que no se conocen quedan en NULL hasta que Ale los complete.
"""
from sqlalchemy import text
from utils.db import engine

WA_NUMEROS = {
    "admin":            "5491165497234",
    "fer_produccion":   "5491165497234",
    "aviation":         "5491165497234",
    "oasis_animal":     "5491165497234",
    "oasis_del_estero": "5491165497234",
    "olivia_coquette":  "5491165497234",
    "francisco_sport":  "5491165497234",
    "constantino_tech": "5491165497234",
    "pharma_delux":     "5491165497234",
    "vkhome_cliente":   None,
    "agustina":         None,
}


def run():
    with engine.begin() as conn:
        for cid, numero in WA_NUMEROS.items():
            if numero is None:
                continue
            conn.execute(
                text("UPDATE lineas_config SET whatsapp_numero=:n WHERE client_id=:cid"),
                {"n": numero, "cid": cid},
            )
    print("migration_v13: whatsapp_numero actualizado en lineas_config.")


if __name__ == "__main__":
    run()
