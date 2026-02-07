# Fastman - The Complete FastAPI CLI Framework

![Fastman Logo](docs/static/img/fastman-logo.jpg)

Fastman is a Laravel-inspired CLI tool for FastAPI. It eliminates boilerplate fatigue by generating project structures, handling database migrations, and scaffolding features, models, and middleware instantly.

Whether you prefer Vertical Slice (Feature) architecture or Layered architecture, Fastman sets it up for you in seconds.

## Features

- **Zero-Dependency Core**: Runs with standard library (Rich/Pyfiglet optional for UI)
- **Smart Package Detection**: Automatically uses `uv`, `poetry`, `pipenv`, or `pip`
- **Multiple Architectures**: Supports `feature` (default), `api`, and `layer` patterns
- **Database Ready**: First-class support for SQLite, PostgreSQL (sync via `psycopg2-binary`), MySQL, Oracle, and Firebase
- **Interactive Shell**: Includes a `tinker` command to interact with your app context
- **Auth Scaffolding**: One-command JWT, OAuth, or Keycloak authentication setup
- **Extensible**: Create custom CLI commands with `make:command`

## Installation

### From PyPI (Coming Soon)

```bash
pip install fastman
```

### From Source (Build)

To install Fastman globally from the source code (e.g., if you've cloned this repository):

**Option 1: Using pipx (Recommended)**
`pipx` installs the tool in an isolated environment so dependencies don't conflict.

```bash
# In the root of the repository
pipx install .
```

**Option 2: Using pip**

```bash
# In the root of the repository
pip install .
```

**Option 3: Using uv**

```bash
# In the root of the repository
uv tool install .
```

Once installed, verify it works:
```bash
fastman --version
```

## Tutorial: Building a Pizza Order API

Let's build a simple API to manage pizza orders to see Fastman in action.

### 1. Create a New Project

We'll use `uv` as our package manager and SQLite for the database.

```bash
fastman new pizza-api --package=uv --database=sqlite
cd pizza-api
```

This creates a new directory `pizza-api` with a virtual environment set up.

### 2. Start the Server

Start the development server to make sure everything is running.

```bash
fastman serve
```

Visit `http://127.0.0.1:8000/docs` to see the Swagger UI. Press `Ctrl+C` to stop the server.

### 3. Create a Feature

We'll use the **Feature Pattern** (Vertical Slice) architecture. Let's create a `orders` feature with full CRUD operations.

```bash
fastman make:feature orders --crud
```

This generates:
- `app/features/orders/models.py`
- `app/features/orders/schemas.py`
- `app/features/orders/service.py`
- `app/features/orders/router.py`

### 4. Define the Data Model

Open `app/features/orders/models.py` and define your pizza order model.

```python
from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.sql import func
from app.core.database import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String(255), nullable=False)
    pizza_type = Column(String(100), nullable=False)
    quantity = Column(Integer, default=1)
    price = Column(Float, nullable=False)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### 5. Update Schemas

Update `app/features/orders/schemas.py` to match your model.

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class OrderBase(BaseModel):
    customer_name: str
    pizza_type: str
    quantity: int = 1
    price: float

class OrderCreate(OrderBase):
    pass

class OrderUpdate(BaseModel):
    status: Optional[str] = None

class OrderRead(OrderBase):
    id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
```

### 6. Database Migrations

Now we need to create the table in the database.

```bash
# Create migration file
fastman make:migration "create orders table"

# Apply migration
fastman migrate
```

### 7. Seed Data (Optional)

Let's add some fake data. Generate a seeder:

```bash
fastman make:seeder OrderSeeder
```

Edit `database/seeders/order_seeder.py` (Fastman installs `faker` automatically):

```python
from sqlalchemy.orm import Session
from app.features.orders.models import Order
from faker import Faker
import random

fake = Faker()

class OrderSeeder:
    @staticmethod
    def run(db: Session):
        pizzas = ["Margherita", "Pepperoni", "Hawaiian", "Veggie"]
        for _ in range(10):
            order = Order(
                customer_name=fake.name(),
                pizza_type=random.choice(pizzas),
                quantity=random.randint(1, 3),
                price=random.uniform(10.0, 25.0),
                status="pending"
            )
            db.add(order)
        db.commit()
```

Run the seeder:
```bash
fastman db:seed --class=OrderSeeder
```

### 8. Test It Out

Start the server again:
```bash
fastman serve
```

Go to `http://127.0.0.1:8000/docs`. You'll see your `Orders` endpoints ready to use!

## Command Reference

### Project Setup

#### `new` - Create a new FastAPI project
```bash
fastman new {name} [--minimal] [--pattern=feature] [--package=uv] [--database=sqlite]
```

**Options:**
- `--pattern`: `feature` (default), `layer`, `api`
- `--package`: `uv`, `poetry`, `pipenv`, `pip`
- `--database`: `sqlite`, `postgresql`, `mysql`, `oracle`, `firebase`

#### `init` - Initialize Fastman in existing project
```bash
fastman init
```

### Scaffolding

#### `make:feature`
Create a vertical slice feature (router, service, model, schema).
```bash
fastman make:feature {name} [--crud]
```

#### `make:api`
Create a simple API endpoint (REST or GraphQL).
```bash
fastman make:api {name} [--style=rest|graphql]
```

#### `make:model`
Create a SQLAlchemy model.
```bash
fastman make:model {name} [--table=custom_name]
```

#### `make:schema`
Create a Pydantic schema.
```bash
fastman make:schema {name}
```

#### `make:service`, `make:repository`, `make:controller`
Create individual architectural components.

#### `make:command`
Create a custom Fastman CLI command.

### Database

- `fastman make:migration {message}`: Create Alembic migration
- `fastman migrate`: Run migrations
- `fastman migrate:rollback [--steps=1]`: Rollback migrations
- `fastman migrate:reset`: Reset database
- `fastman make:seeder {name}`: Create data seeder
- `fastman db:seed [--class=Name]`: Run seeders

### Authentication

Install full authentication system (Models, JWT logic, Routes).
```bash
fastman install:auth --type=jwt
```

### Utilities

- `fastman serve`: Start dev server
- `fastman tinker`: Interactive shell with DB session
- `fastman generate:key`: Generate secret key
- `fastman optimize`: Format and clean code (using black/isort/autoflake)
- `fastman build --docker`: Generate Dockerfile

## Contributing

Fastman is open source! Contributions are welcome.

Repository: https://github.com/fastman/fastman

## License

This project is licensed under the **MIT License**.
