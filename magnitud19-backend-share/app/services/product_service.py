from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


def get_by_id(db: Session, tenant_id: str, product_id: str) -> Optional[Product]:
    stmt = select(Product).where(Product.tenant_id == tenant_id, Product.id == product_id)
    return db.execute(stmt).scalars().first()


def get_by_sku(db: Session, tenant_id: str, sku: str) -> Optional[Product]:
    stmt = select(Product).where(Product.tenant_id == tenant_id, Product.sku == sku)
    return db.execute(stmt).scalars().first()


def get_multi(db: Session, tenant_id: str, skip: int = 0, limit: int = 100) -> List[Product]:
    stmt = (
        select(Product)
        .where(Product.tenant_id == tenant_id)
        .offset(skip)
        .limit(limit)
    )
    return db.execute(stmt).scalars().all()


def get_by_client(db: Session, tenant_id: str, client_id: str, skip: int = 0, limit: int = 100) -> List[Product]:
    stmt = (
        select(Product)
        .where(Product.tenant_id == tenant_id, Product.client_id == client_id)
        .offset(skip)
        .limit(limit)
    )
    return db.execute(stmt).scalars().all()


def create(db: Session, product_in: ProductCreate) -> Product:
    db_obj = Product(**product_in.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update(db: Session, db_obj: Product, payload: ProductUpdate) -> Product:
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(db_obj, k, v)

    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


