from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.store import Store
from app.schemas.store import StoreCreate


def get_by_slug(db: Session, slug: str) -> Optional[Store]:
    stmt = select(Store).where(Store.slug == slug)
    return db.execute(stmt).scalars().first()


def get_multi(db: Session, skip: int = 0, limit: int = 100) -> List[Store]:
    stmt = select(Store).offset(skip).limit(limit)
    return db.execute(stmt).scalars().all()


def create(db: Session, payload: StoreCreate) -> Store:
    obj = Store(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj
