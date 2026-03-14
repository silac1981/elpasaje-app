import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )

    name: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
