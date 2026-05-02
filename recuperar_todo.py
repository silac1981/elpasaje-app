from app.db.session import SessionLocal
from app.models.product import Product

db = SessionLocal()

def recuperar_catalogo():
    productos = db.query(Product).all()
    print(f"⏳ Analizando {len(productos)} productos...")
    
    for p in productos:
        # Lógica de asignación por palabras clave
        name = p.name.lower()
        if "moño" in name or "coquette" in name:
            p.client_id = "olivia_coquette"
        elif "sport" in name or "escudo" in name or "flexible" in name:
            p.client_id = "francisco_sport"
        elif "sacra" in name or "virtuosa" in name or "cruz" in name:
            p.client_id = "mujeres_virtuosas"
        else:
            p.client_id = "admin" # Magnitud 19 / Alejandra
            
    db.commit()
    print("🚀 ¡Catálogo reorganizado! Ahora cada socio verá sus productos.")

if __name__ == "__main__":
    recuperar_catalogo()