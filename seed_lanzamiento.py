from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.models.tenant import Tenant
from app.models.product import Product

# Aseguramos que las tablas existan con el formato correcto
Base.metadata.create_all(bind=engine)

db = SessionLocal()

def ejecutar_lanzamiento_total():
    # 1. Registro de Socios (Incluyendo La Solidaria)
    socios = [
        {"id": "olivia_coquette", "name": "Olivia - Coquette", "slug": "olivia-coquette"},
        {"id": "francisco_sport", "name": "Francisco - Sport", "slug": "francisco-sport"},
        {"id": "nely_sacra", "name": "Nely - Línea Sacra", "slug": "nely-sacra"},
        {"id": "project_hub", "name": "Project Hub - B2B", "slug": "project-hub"},
        {"id": "la_solidaria", "name": "La Solidaria - Impacto", "slug": "la-solidaria"}
    ]
    
    print("⏳ Registrando líneas familiares y solidarias...")
    for s in socios:
        if not db.query(Tenant).filter_by(id=s["id"]).first():
            db.add(Tenant(**s))
    db.commit()

    # 2. Carga de Productos de Vanguardia y Solidarios
    productos = [
        # PRODUCTO SOLIDARIO (RECICLAJE)
        Product(sku="SOL-REC-HUE", client_id="la_solidaria", 
                name="Llavero Huellita - Oasis Animal", 
                category="Solidaria", price=800.0, cost=50.0, stock=100,
                description="100% Plástico Reciclado. Donación directa al refugio."),
        
        # PRODUCTO SOLIDARIO (NIÑOS)
        Product(sku="SOL-REC-FID", client_id="la_solidaria", 
                name="Fidget Anti-estrés - Mentes Brillantes", 
                category="Solidaria", price=1200.0, cost=100.0, stock=50,
                description="Ayuda a niños con enfermedades mentales."),

        # PRODUCTO PROJECT HUB (B2B)
        Product(sku="HUB-EXT-01", client_id="project_hub", 
                name="[Project Hub] Impresión Externa", 
                category="B2B", price=0.0, cost=0.0, stock=0,
                description="Servicio de impresión para terceros.")
    ]

    print("⏳ Activando productos de impacto social...")
    for p in productos:
        if not db.query(Product).filter_by(sku=p.sku).first():
            db.add(p)
    
    db.commit()
    print("🚀 ¡SISTEMA COMPLETO! Líneas familiares, B2B y Solidaria cargadas.")

if __name__ == "__main__":
    ejecutar_lanzamiento_total()