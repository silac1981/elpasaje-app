from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.services import product_service

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=ProductResponse)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    existing = product_service.get_by_sku(db, tenant_id=payload.tenant_id, sku=payload.sku)
    if existing:
        raise HTTPException(status_code=400, detail="El SKU ya existe en este tenant")
    return product_service.create(db=db, product_in=payload)


@router.get("/", response_model=List[ProductResponse])
def list_products(tenant_id: str, db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    return product_service.get_multi(db=db, tenant_id=tenant_id, skip=skip, limit=limit)


@router.get("/by-client/{client_id}", response_model=List[ProductResponse])
def list_products_by_client(client_id: str, tenant_id: str, db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    return product_service.get_by_client(db=db, tenant_id=tenant_id, client_id=client_id, skip=skip, limit=limit)


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(product_id: str, tenant_id: str, payload: ProductUpdate, db: Session = Depends(get_db)):
    db_obj = product_service.get_by_id(db, tenant_id=tenant_id, product_id=product_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product_service.update(db=db, db_obj=db_obj, payload=payload)




