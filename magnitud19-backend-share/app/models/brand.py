import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class Brand(Base):
    __tablename__ = "brands"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )

    tenant_id: Mapped[str] = mapped_column(String, ForeignKey("tenants.id"), index=True, nullable=False)

    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, index=True, nullable=False)

    active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
