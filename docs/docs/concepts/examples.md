---
sidebar_position: 4
---

# Architecture Examples

Real-world examples for each architecture pattern.

---

## Feature Pattern: E-Commerce API

A product catalog with orders and user management.

### Create the Project

```bash
fastman new ecommerce-api --pattern=feature --database=postgresql
cd ecommerce-api
```

### Scaffold Features

```bash
fastman make:feature product --crud
fastman make:feature order --crud
fastman make:feature user --crud
fastman install:auth jwt
```

### Project Structure

```
app/
├── core/
│   ├── config.py
│   ├── database.py
│   └── dependencies.py
│
├── features/
│   ├── auth/                    # JWT authentication
│   │   ├── dependencies.py
│   │   ├── models.py
│   │   ├── router.py
│   │   ├── schemas.py
│   │   ├── security.py
│   │   └── service.py
│   │
│   ├── product/                 # Product catalog
│   │   ├── models.py
│   │   ├── router.py
│   │   ├── schemas.py
│   │   └── service.py
│   │
│   ├── order/                   # Order management
│   │   ├── models.py
│   │   ├── router.py
│   │   ├── schemas.py
│   │   └── service.py
│   │
│   └── user/                    # User profiles
│       ├── models.py
│       ├── router.py
│       ├── schemas.py
│       └── service.py
│
└── main.py
```

### Example: Product Feature

```python
# app/features/product/models.py
from sqlalchemy import Column, Integer, String, Numeric, Text
from app.core.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    price = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, default=0)
```

```python
# app/features/product/schemas.py
from pydantic import BaseModel
from decimal import Decimal

class ProductBase(BaseModel):
    name: str
    description: str | None = None
    price: Decimal
    stock: int = 0

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int

    class Config:
        from_attributes = True
```

```python
# app/features/product/service.py
from sqlalchemy.orm import Session
from .models import Product
from .schemas import ProductCreate

class ProductService:
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100):
        return db.query(Product).offset(skip).limit(limit).all()

    @staticmethod
    def get_by_id(db: Session, product_id: int):
        return db.query(Product).filter(Product.id == product_id).first()

    @staticmethod
    def create(db: Session, product: ProductCreate):
        db_product = Product(**product.model_dump())
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        return db_product
```

```python
# app/features/product/router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from .schemas import ProductCreate, ProductResponse
from .service import ProductService

router = APIRouter(prefix="/products", tags=["products"])

@router.get("/", response_model=list[ProductResponse])
def list_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return ProductService.get_all(db, skip, limit)

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = ProductService.get_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.post("/", response_model=ProductResponse, status_code=201)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    return ProductService.create(db, product)
```

---

## API Pattern: Blog API

A simple blog with versioned API.

### Create the Project

```bash
fastman new blog-api --pattern=api --database=sqlite
cd blog-api
```

### Project Structure

```
app/
├── api/
│   ├── v1/
│   │   ├── __init__.py
│   │   ├── posts.py           # /api/v1/posts
│   │   ├── comments.py        # /api/v1/comments
│   │   └── authors.py         # /api/v1/authors
│   │
│   └── v2/
│       └── posts.py           # /api/v2/posts (new version)
│
├── models/
│   ├── post.py
│   ├── comment.py
│   └── author.py
│
├── schemas/
│   ├── post.py
│   ├── comment.py
│   └── author.py
│
├── core/
│   ├── config.py
│   └── database.py
│
└── main.py
```

### Example: Posts API

```python
# app/models/post.py
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True)
    content = Column(Text)
    author_id = Column(Integer, ForeignKey("authors.id"))
    published_at = Column(DateTime, server_default=func.now())

    author = relationship("Author", back_populates="posts")
    comments = relationship("Comment", back_populates="post")
```

```python
# app/api/v1/posts.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.post import Post
from app.schemas.post import PostResponse, PostCreate

router = APIRouter()

@router.get("/posts")
def list_posts(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    skip = (page - 1) * per_page
    posts = db.query(Post).offset(skip).limit(per_page).all()
    total = db.query(Post).count()
    
    return {
        "data": posts,
        "meta": {
            "page": page,
            "per_page": per_page,
            "total": total
        }
    }

@router.get("/posts/{slug}")
def get_post(slug: str, db: Session = Depends(get_db)):
    return db.query(Post).filter(Post.slug == slug).first()
```

```python
# app/main.py
from fastapi import FastAPI
from app.api.v1 import posts as v1_posts
from app.api.v2 import posts as v2_posts

app = FastAPI(title="Blog API")

# API versioning
app.include_router(v1_posts.router, prefix="/api/v1", tags=["v1"])
app.include_router(v2_posts.router, prefix="/api/v2", tags=["v2"])
```

---

## Layer Pattern: Enterprise CRM

A complex CRM with clear separation of concerns.

### Create the Project

```bash
fastman new crm-api --pattern=layer --database=postgresql
cd crm-api
```

### Project Structure

```
app/
├── controllers/                 # Request handling
│   ├── customer_controller.py
│   ├── contact_controller.py
│   └── deal_controller.py
│
├── services/                    # Business logic
│   ├── customer_service.py
│   ├── contact_service.py
│   └── deal_service.py
│
├── repositories/                # Data access
│   ├── base_repository.py
│   ├── customer_repository.py
│   ├── contact_repository.py
│   └── deal_repository.py
│
├── models/                      # Database models
│   ├── customer.py
│   ├── contact.py
│   └── deal.py
│
├── schemas/                     # DTOs
│   ├── customer.py
│   ├── contact.py
│   └── deal.py
│
├── core/
│   ├── config.py
│   └── database.py
│
└── main.py
```

### Example: Customer Module

```python
# app/repositories/base_repository.py
from typing import TypeVar, Generic, Type
from sqlalchemy.orm import Session

T = TypeVar("T")

class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T], db: Session):
        self.model = model
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 100):
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def get_by_id(self, id: int):
        return self.db.query(self.model).filter(self.model.id == id).first()

    def create(self, data: dict):
        instance = self.model(**data)
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def update(self, id: int, data: dict):
        instance = self.get_by_id(id)
        if instance:
            for key, value in data.items():
                setattr(instance, key, value)
            self.db.commit()
            self.db.refresh(instance)
        return instance

    def delete(self, id: int):
        instance = self.get_by_id(id)
        if instance:
            self.db.delete(instance)
            self.db.commit()
        return instance
```

```python
# app/repositories/customer_repository.py
from sqlalchemy.orm import Session
from app.models.customer import Customer
from .base_repository import BaseRepository

class CustomerRepository(BaseRepository[Customer]):
    def __init__(self, db: Session):
        super().__init__(Customer, db)

    def find_by_email(self, email: str):
        return self.db.query(Customer).filter(Customer.email == email).first()

    def find_active(self):
        return self.db.query(Customer).filter(Customer.is_active == True).all()
```

```python
# app/services/customer_service.py
from sqlalchemy.orm import Session
from app.repositories.customer_repository import CustomerRepository
from app.schemas.customer import CustomerCreate

class CustomerService:
    def __init__(self, db: Session):
        self.repo = CustomerRepository(db)

    def get_customers(self, skip: int = 0, limit: int = 100):
        return self.repo.get_all(skip, limit)

    def get_customer(self, customer_id: int):
        return self.repo.get_by_id(customer_id)

    def create_customer(self, data: CustomerCreate):
        # Business logic: check for duplicate email
        existing = self.repo.find_by_email(data.email)
        if existing:
            raise ValueError("Customer with this email already exists")
        
        return self.repo.create(data.model_dump())
```

```python
# app/controllers/customer_controller.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.customer_service import CustomerService
from app.schemas.customer import CustomerCreate, CustomerResponse

router = APIRouter(prefix="/customers", tags=["customers"])

def get_service(db: Session = Depends(get_db)):
    return CustomerService(db)

@router.get("/", response_model=list[CustomerResponse])
def list_customers(service: CustomerService = Depends(get_service)):
    return service.get_customers()

@router.post("/", response_model=CustomerResponse, status_code=201)
def create_customer(
    data: CustomerCreate,
    service: CustomerService = Depends(get_service)
):
    try:
        return service.create_customer(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

## Comparison Summary

| Aspect | Feature | API | Layer |
|--------|---------|-----|-------|
| **Organization** | By domain | By version | By concern |
| **Best for** | Medium-large apps | Simple APIs | Enterprise |
| **Scalability** | Extract to microservices | Add versions | Add layers |
| **Learning curve** | Low | Low | Medium |
| **Code locality** | High | Medium | Low |
