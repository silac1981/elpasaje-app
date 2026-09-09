"""migration_v14.py — Cambiar visibilidad OE-* (vkhome_cliente) de 'publico' a 'socio'.

Los 9 productos OE-* tienen client_id='vkhome_cliente' (línea de Agustina).
Estaban marcados visibilidad='publico' pero no hay página HTML pública para esa línea.
Agustina los gestiona desde su panel multi-línea → deben ser 'socio', no 'publico'.
"""
from sqlalchemy import text
from utils.db import engine

SKU_OE = [
    "OE-BAS-M",
    "OE-BAS-S",
    "OE-BDA-U",
    "OE-BOV-L",
    "OE-BOV-M",
    "OE-BOV-S",
    "OE-BRR-M",
    "OE-BRR-S",
    "OE-SAR-U",
]


def run():
    with engine.begin() as conn:
        result = conn.execute(
            text(
                "UPDATE products SET visibilidad='socio' "
                "WHERE sku IN :skus AND visibilidad='publico'"
            ),
            {"skus": tuple(SKU_OE)},
        )
        changed = result.rowcount
    print(f"migration_v14: {changed} productos OE-* → visibilidad='socio'.")


if __name__ == "__main__":
    run()
