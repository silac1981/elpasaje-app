from app.db.session import SessionLocal
from app.models.product import Product

db = SessionLocal()

def recuperar():
    # Buscamos productos que quedaron "huérfanos" y los asignamos
    productos = db.query(Product).all()
    for p in productos:
        if "Moño" in p.name or "Coquette" in p.name:
            p.client_id = "olivia_coquette"
        elif "Sport" in p.name or "Escudo" in p.name:
            p.client_id = "francisco_sport"
        elif "Sacra" in p.name or "Virtuosas" in p.name:
            p.client_id = "mujeres_virtuosas"
        else:
            p.client_id = "admin" # O el ID de Alejandra
    
    db.commit()
    print("✅ Catálogo reorganizado por líneas familiares.")

recuperar()