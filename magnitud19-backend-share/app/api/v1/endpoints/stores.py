from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.schemas.store import StoreCreate, StoreResponse
from app.services import store_service

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=StoreResponse)
def create_store(payload: StoreCreate, db: Session = Depends(get_db)):
    existing = store_service.get_by_slug(db, slug=payload.slug)
    if existing:
        raise HTTPException(status_code=400, detail="El slug ya existe")
    return store_service.create(db, payload=payload)

@router.get("/", response_model=List[StoreResponse])
def read_stores(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return store_service.get_multi(db, skip=skip, limit=limit)
