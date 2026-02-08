---
sidebar_position: 2
---

# Directory Structure

Understanding how Fastman organizes your code.

## Feature Pattern (Default)

The feature pattern uses **vertical slices**—each feature contains everything it needs.

```
my-api/
├── app/
│   ├── core/                    # Shared infrastructure
│   │   ├── __init__.py
│   │   ├── config.py            # Settings from environment
│   │   ├── database.py          # SQLAlchemy session
│   │   └── dependencies.py      # FastAPI dependencies
│   │
│   ├── features/                # Feature modules
│   │   ├── user/
│   │   │   ├── __init__.py
│   │   │   ├── models.py        # User SQLAlchemy model
│   │   │   ├── schemas.py       # User Pydantic schemas
│   │   │   ├── service.py       # User business logic
│   │   │   └── router.py        # User API endpoints
│   │   │
│   │   └── post/
│   │       ├── models.py
│   │       ├── schemas.py
│   │       ├── service.py
│   │       └── router.py
│   │
│   └── main.py                  # App entry point
│
├── database/
│   ├── migrations/              # Alembic migrations
│   │   └── versions/
│   └── seeders/                 # Database seeders
│
├── tests/
│   ├── factories/               # Model factories
│   └── test_*.py                # Test files
│
├── .env                         # Environment variables
├── alembic.ini                  # Migration config
└── pyproject.toml               # Dependencies
```

## API Pattern

The API pattern groups code by HTTP resource:

```
app/
├── api/
│   ├── v1/
│   │   ├── users.py
│   │   └── posts.py
│   └── v2/
├── models/
├── schemas/
└── services/
```

## Layer Pattern

The layer pattern separates by technical concern:

```
app/
├── controllers/
├── models/
├── repositories/
├── schemas/
└── services/
```

## Key Files

| File | Purpose |
|------|---------|
| `app/main.py` | Application factory, router mounting |
| `app/core/config.py` | Pydantic settings from `.env` |
| `app/core/database.py` | SQLAlchemy engine and session |
| `alembic.ini` | Database migration configuration |
| `.env` | Environment variables (never commit!) |
