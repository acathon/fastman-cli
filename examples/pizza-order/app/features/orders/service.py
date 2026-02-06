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
