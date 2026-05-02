from database_engine import session, Tenant

def inicializar_familia():
    # Definimos los socios con su rol actual
    socios = [
        # Oasis del Estero: Hoy marca propia (Hidroponia), mañana puede ser revendedor
        Tenant(id='oasis_estero', name='Oasis del Estero - Fede', schema_type='MARCA_PROPIA'),
        
        # Oasis Animal: Marca propia + Promo cruzada
        Tenant(id='oasis_animal', name='Oasis Animal - Agustina', schema_type='MARCA_PROPIA'),
        
        # Revendedores puros por ahora
        Tenant(id='pharma_delux', name='Pharma DeLux - Lucas', schema_type='REVENDEDOR'),
        Tenant(id='aviation_nando', name='Aviation - Nando', schema_type='REVENDEDOR')
    ]
    
    for s in socios:
        existente = session.query(Tenant).filter_by(id=s.id).first()
        if not existente:
            session.add(s)
            print(f"✅ Socio creado: {s.name}")
        else:
            # Si ya existe, actualizamos el nombre o tipo por si cambió
            existente.name = s.name
            existente.schema_type = s.schema_type
            print(f"🔄 Socio actualizado: {s.name}")
    
    session.commit()
    print("\n🚀 Base de datos de la Familia lista para operar.")

if __name__ == "__main__":
    inicializar_familia()