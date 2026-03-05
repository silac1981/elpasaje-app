import enum
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class ClientType(str, enum.Enum):
    individual = "individual"
    corporate = "corporate"
    government = "government"
    vip = "vip"


class ClientBase(BaseModel):
    tenant_id: str
    contact_name: str
    email: EmailStr
    company_name: Optional[str] = None
    phone: Optional[str] = None
    type: ClientType = ClientType.individual


class ClientCreate(ClientBase):
    pass


class ClientResponse(ClientBase):
    id: str
    status: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ClientResponse(ClientBase):
    id: str
    status: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
