from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.schemas.client import ClientCreate, ClientResponse
from app.services import client_service

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=ClientResponse)
def create_client(payload: ClientCreate, db: Session = Depends(get_db)):
    existing = client_service.get_by_email(db, tenant_id=payload.tenant_id, email=str(payload.email))
    if existing:
        raise HTTPException(status_code=400, detail="El email ya existe en este tenant")
    return client_service.create(db=db, client_in=payload)


@router.get("/", response_model=List[ClientResponse])
def list_clients(tenant_id: str, db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    return client_service.get_multi(db=db, tenant_id=tenant_id, skip=skip, limit=limit)

