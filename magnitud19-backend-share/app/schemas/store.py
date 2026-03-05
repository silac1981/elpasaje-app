from pydantic import BaseModel, ConfigDict
from datetime import datetime


class StoreCreate(BaseModel):
    name: str
    slug: str
    type: str = "partner"


class StoreResponse(StoreCreate):
    id: str
    active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
