from database_engine import session, Product, Material

def cargar_todo():
    # 1. Aseguramos materiales base (PLA para casi todo, PETG para Fede)
    pla = Material(name="PLA Premium", color="Blanco", stock_gr=2000.0, cost_per_gr=18.0)
    petg = Material(name="PETG Alta Resistencia", color="Negro", stock_gr=1500.0, cost_per_gr=25.0)
    session.add_all([pla, petg])
    session.flush()

    # 2. Definición de Catálogo por Línea
    productos = [
        # OASIS ANIMAL (Agus)
        Product(tenant_id='oasis_animal', material_id=pla.id, sku='OA-MAT-01', name='Mate Pampa Animal Print', weight_gr=120, price_x3=4500, 
                image_url="https://acdn.mitiendanube.com/stores/001/165/154/products/mate-pampa-animal-print1-6677f2d594532e185d15886025178927-640-0.jpg"),
        
        # PHARMA DELUX (Lucas)
        Product(tenant_id='pharma_delux', material_id=pla.id, sku='PH-ORG-01', name='Organizador de instrumental Premium', weight_gr=250, price_x3=8500,
                image_url="https://m.media-amazon.com/images/I/71Yv0-4+DkL._AC_SL1500_.jpg"),
        
        # AVIATION (Nando)
        Product(tenant_id='aviation_nando', material_id=petg.id, sku='AV-SOP-01', name='Soporte Tablet para Cabina', weight_gr=180, price_x3=12000,
                image_url="https://m.media-amazon.com/images/I/61k8C-vH0OL._AC_SL1500_.jpg"),
        
        # OASIS DEL ESTERO (Fede - Hidroponia)
        Product(tenant_id='oasis_estero', material_id=petg.id, sku='HIDRO-001', name='Soporte Canasta Hidropónica 3"', weight_gr=45, price_x3=1200,
                image_url="https://m.media-amazon.com/images/I/61NAs6mXp9L._AC_UF1000,1000_QL80_.jpg")
    ]

    for p in productos:
        # Evitamos duplicar si ya existen por el SKU
        existente = session.query(Product).filter_by(sku=p.sku).first()
        if not existente:
            session.add(p)
    
    session.commit()
    print("✅ Catálogo completo cargado: Oasis Animal, Pharma, Aviation e Hidroponia listos.")

if __name__ == "__main__":
    cargar_todo()