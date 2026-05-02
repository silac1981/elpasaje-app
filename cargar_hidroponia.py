from database_engine import session, Product, Material

def cargar_primeros_productos():
    # 1. Material
    petg = Material(name="PETG Premium", color="Negro", stock_gr=1000.0, cost_per_gr=25.0)
    session.add(petg)
    session.flush() 

    # 2. Producto con FOTO
    maceta = Product(
        tenant_id='oasis_estero',
        material_id=petg.id,
        sku='HIDRO-001',
        name='Soporte Canasta Hidropónica 3"',
        weight_gr=45.0,
        price_x3=1200.0,
        image_url="https://m.media-amazon.com/images/I/61NAs6mXp9L._AC_UF1000,1000_QL80_.jpg" # <--- ¡FOTO!
    )
    
    session.add(maceta)
    session.commit()
    print(f"🌱 Producto con foto cargado con éxito.")

if __name__ == "__main__":
    cargar_primeros_productos()