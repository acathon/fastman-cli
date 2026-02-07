from sqlalchemy import Column, Integer, String, Float, JSON
from app.core.database import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, index=True)
    items = Column(JSON)  # List of pizza names
    total_price = Column(Float)
    status = Column(String, default="pending")
