from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.schemas.tenant import TenantCreate, TenantResponse
from app.services import tenant_service

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=TenantResponse)
def create_tenant(payload: TenantCreate, db: Session = Depends(get_db)):
    existing = tenant_service.get_by_slug(db, slug=payload.slug)
    if existing:
        raise HTTPException(status_code=400, detail="El slug ya existe")
    return tenant_service.create(db, tenant_in=payload)

@router.get("/", response_model=List[TenantResponse])
def read_tenants(db: Session = Depends(get_db)):
    return tenant_service.get_multi(db)
