from app.db.session import SessionLocal
from app.models.tenant import Tenant
from app.models.product import Product

db = SessionLocal()

def verificar():
    print("--- 🏛️ SOCIOS REGISTRADOS ---")
    tenants = db.query(Tenant).all()
    for t in tenants:
        print(f"Socio: {t.name} | Slug: {t.slug}")

    print("\n--- 📦 PRODUCTOS EN CATÁLOGO ---")
    products = db.query(Product).all()
    for p in products:
        print(f"SKU: {p.sku} | Nombre: {p.name} | Precio: ${p.price}")

verificar()