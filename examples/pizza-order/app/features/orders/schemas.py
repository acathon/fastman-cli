from pydantic import BaseModel
from typing import List

class OrderBase(BaseModel):
    customer_name: str
    items: List[str]

class OrderCreate(OrderBase):
    pass

class OrderResponse(OrderBase):
    id: int
    total_price: float
    status: str

    class Config:
        from_attributes = True
