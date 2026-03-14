from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tenant import Tenant
from app.schemas.tenant import TenantCreate


def get_by_slug(db: Session, slug: str) -> Optional[Tenant]:
    stmt = select(Tenant).where(Tenant.slug == slug)
    return db.execute(stmt).scalars().first()


def get_multi(db: Session) -> List[Tenant]:
    stmt = select(Tenant).order_by(Tenant.created_at.desc())
    return db.execute(stmt).scalars().all()


def create(db: Session, tenant_in: TenantCreate) -> Tenant:
    db_obj = Tenant(name=tenant_in.name, slug=tenant_in.slug)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj
