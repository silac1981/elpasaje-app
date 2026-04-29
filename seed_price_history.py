"""
seed_price_history.py
Pobla price_history con los precios actuales de todos los productos.
Corre una vez: python seed_price_history.py
"""
import os
from sqlalchemy import create_engine, text

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "elpasaje_v2.db")
engine = create_engine(f"sqlite:///{DB_PATH}")

with engine.connect() as conn:
    existing = conn.execute(text("SELECT COUNT(*) FROM price_history")).scalar()
    if existing > 0:
        print(f"Ya hay {existing} registros en price_history. Usá --force para re-seedear.")
    else:
        products = conn.execute(text("SELECT sku, price FROM products")).fetchall()
        for sku, price in products:
            conn.execute(text("""
                INSERT INTO price_history (product_sku, precio_anterior, precio_nuevo, motivo)
                VALUES (:sku, :price, :price, 'seed inicial — precio base Abr 2026')
            """), {"sku": sku, "price": price})
        conn.commit()
        print(f"Seed completo: {len(products)} productos cargados en price_history (base Abr 2026).")
