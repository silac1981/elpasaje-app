from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ProductBase(BaseModel):
    tenant_id: str
    client_id: str
    sku: str
    name: str
    description: Optional[str] = None
    price: float
    cost: float
    stock: int = 0
    category: Optional[str] = None
    active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    sku: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    cost: Optional[float] = None
    stock: Optional[int] = None
    category: Optional[str] = None
    active: Optional[bool] = None


class ProductResponse(ProductBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


