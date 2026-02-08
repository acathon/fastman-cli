---
sidebar_position: 3
---

# Database & Migrations

Fastman uses SQLAlchemy for the ORM and Alembic for migrations.

## Supported Databases

| Database | Connection String |
|----------|------------------|
| SQLite | `sqlite:///./app.db` |
| PostgreSQL | `postgresql://user:pass@host:5432/db` |
| MySQL | `mysql+pymysql://user:pass@host:3306/db` |
| Oracle | `oracle+cx_oracle://user:pass@host:1521/db` |
| Firebase | Custom integration (no Alembic) |

## Configuration

Set your database URL in `.env`:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/myapp
```

## Models

Create models with `make:model`:

```bash
fastman make:model post
```

```python
# app/features/post/models.py
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
```

## Migrations

### Create a Migration

```bash
fastman make:migration "create posts table"
```

This generates a timestamped migration in `database/migrations/versions/`.

### Run Migrations

```bash
# Apply all pending migrations
fastman database:migrate

# Check current status
fastman migrate:status
```

### Rollback

```bash
# Rollback last migration
fastman migrate:rollback

# Rollback multiple
fastman migrate:rollback --steps=3

# Reset everything (danger!)
fastman migrate:reset
```

## Seeders

Populate your database with initial or test data.

### Create a Seeder

```bash
fastman make:seeder user
```

```python
# database/seeders/user_seeder.py
from app.features.user.models import User
from passlib.hash import bcrypt

class UserSeeder:
    @staticmethod
    def run(db):
        admin = User(
            email="admin@example.com",
            password=bcrypt.hash("password123"),
            is_admin=True
        )
        db.add(admin)
        db.commit()
        print("Created admin user")
```

### Run Seeders

```bash
# Run all seeders
fastman database:seed

# Run specific seeder
fastman database:seed --class=UserSeeder
```

:::warning Important
Always run seeder commands from your **project root** directory.
:::

## Factories

Create realistic test data with Faker.

```bash
fastman make:factory user
```

```python
# tests/factories/user_factory.py
from faker import Faker

fake = Faker()

class UserFactory:
    @staticmethod
    def make(**kwargs):
        return {
            "email": kwargs.get("email", fake.email()),
            "name": kwargs.get("name", fake.name()),
            "password": kwargs.get("password", "testpass123"),
        }
    
    @staticmethod
    def create(db, **kwargs):
        from app.features.user.models import User
        user = User(**UserFactory.make(**kwargs))
        db.add(user)
        db.commit()
        return user
```
