from pydantic import BaseModel, ConfigDict
from datetime import datetime


class TenantBase(BaseModel):
    name: str
    slug: str


class TenantCreate(TenantBase):
    pass


class TenantResponse(TenantBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
