import uuid
import enum
from datetime import datetime

from sqlalchemy import String, Boolean, DateTime, Enum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class ClientType(str, enum.Enum):
    individual = "individual"
    corporate = "corporate"
    government = "government"
    vip = "vip"


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )

    # Multi-tenant
    tenant_id: Mapped[str] = mapped_column(
        String, ForeignKey("tenants.id"), index=True, nullable=False
    )

    company_name: Mapped[str | None] = mapped_column(String, nullable=True)
    contact_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, index=True, nullable=False)  # unique por tenant (lo hacemos después)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)

    type: Mapped[ClientType] = mapped_column(
        Enum(ClientType), default=ClientType.individual, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    status: Mapped[bool] = mapped_column(Boolean, default=True)

