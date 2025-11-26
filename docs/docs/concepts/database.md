---
sidebar_position: 2
---

# Database & Migrations

Fastman treats the database as a first-class citizen. It wraps **SQLAlchemy** and **Alembic** to provide a seamless experience.

## Supported Databases

- **SQLite** (Default)
- **PostgreSQL**
- **MySQL**
- **Oracle**
- **Firebase** (via specialized driver)

## Migrations

Forget manual Alembic commands. Fastman provides intuitive wrappers:

| Command | Equivalent Alembic Command |
|---------|----------------------------|
| `fastman make:migration "msg"` | `alembic revision --autogenerate -m "msg"` |
| `fastman migrate` | `alembic upgrade head` |
| `fastman migrate:rollback` | `alembic downgrade -1` |

## Models

Models are defined using SQLAlchemy declarative base.

```python
from app.core.database import Base
from sqlalchemy import Column, Integer, String

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
```

## Seeding

Fastman includes a seeder system to populate your database with test data.

1.  Create a seeder: `fastman make:seeder UserSeeder`
2.  Run seeders: `fastman db:seed`
