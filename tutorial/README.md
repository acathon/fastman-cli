# Building a Pizza Ordering App with Fastman

This tutorial guides you through building a simple Pizza Ordering API using Fastman. We will use Fastman's feature-based architecture to organize our code.

## Prerequisites

- Python 3.9+
- `fastman` installed (`pip install fastman` or `uv tool install fastman`)

## 1. Create a New Project

First, generate a new Fastman project.

```bash
fastman new pizza-order
cd pizza-order
```

This creates a new directory `pizza-order` with the standard Fastman project structure.

## 2. Generate a Feature

Fastman encourages a "Vertical Slice" architecture. Instead of separating code by type (controllers, models), we separate by feature.

Let's create an `orders` feature.

```bash
fastman make:feature orders
```

This creates `app/features/orders/` with the following files:
- `router.py`: API endpoints
- `models.py`: Database models
- `schemas.py`: Pydantic schemas
- `service.py`: Business logic

## 3. Define the Data Model

Open `app/features/orders/models.py` and define the `Order` model.

```python
from sqlalchemy import Column, Integer, String, Float, JSON
from app.core.database import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, index=True)
    items = Column(JSON)  # List of pizza names
    total_price = Column(Float)
    status = Column(String, default="pending")
```

## 4. Define Schemas

Open `app/features/orders/schemas.py` and define the request/response schemas.

```python
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
```

## 5. Implement Business Logic

Open `app/features/orders/service.py`.

```python
from sqlalchemy.orm import Session
from . import models, schemas

PIZZA_PRICES = {
    "margherita": 10.0,
    "pepperoni": 12.0,
    "veggie": 11.0
}

def create_order(db: Session, order: schemas.OrderCreate):
    total_price = sum(PIZZA_PRICES.get(item.lower(), 10.0) for item in order.items)

    db_order = models.Order(
        customer_name=order.customer_name,
        items=order.items,
        total_price=total_price,
        status="pending"
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

def get_orders(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Order).offset(skip).limit(limit).all()
```

## 6. Define Routes

Open `app/features/orders/router.py`.

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from . import schemas, service

router = APIRouter(prefix="/orders", tags=["orders"])

@router.post("/", response_model=schemas.OrderResponse)
def create_order(order: schemas.OrderCreate, db: Session = Depends(get_db)):
    return service.create_order(db=db, order=order)

@router.get("/", response_model=List[schemas.OrderResponse])
def read_orders(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return service.get_orders(db, skip=skip, limit=limit)
```

## 7. Database Migrations

Create a migration for the new table.

```bash
fastman make:migration "create orders table"
fastman migrate
```

## 8. Run the Server

Start the development server.

```bash
fastman serve
```

Visit `http://localhost:8000/docs` to see your API in action.

## 9. List Routes

You can list all registered routes using:

```bash
fastman route:list
```

This should show your new `/orders` endpoints.
