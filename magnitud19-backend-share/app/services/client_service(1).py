from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.client import Client
from app.schemas.client import ClientCreate


def get_by_id(db: Session, client_id: str) -> Optional[Client]:
    stmt = select(Client).where(Client.id == client_id)
    return db.execute(stmt).scalars().first()


def get_by_email(db: Session, tenant_id: str, email: str) -> Optional[Client]:
    stmt = select(Client).where(Client.tenant_id == tenant_id, Client.email == email)
    return db.execute(stmt).scalars().first()


def get_multi(db: Session, tenant_id: str, skip: int = 0, limit: int = 100) -> List[Client]:
    stmt = (
        select(Client)
        .where(Client.tenant_id == tenant_id)
        .offset(skip)
        .limit(limit)
    )
    return db.execute(stmt).scalars().all()


def create(db: Session, client_in: ClientCreate) -> Client:
    db_obj = Client(**client_in.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

