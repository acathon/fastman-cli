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
├── public/                      # Static files (HTML, images, CSS, JS)
├── database/
│   ├── migrations/              # Alembic migrations
│   │   └── versions/
│   └── seeders/                 # Database seeders
│
├── tests/
│   ├── factories/               # Model factories
│   └── test_*.py                # Test files
│
├── .env                         # Default environment variables
├── .env.development             # Development settings
├── .env.staging                 # Staging settings
├── .env.production              # Production settings
├── alembic.ini                  # Migration config
└── pyproject.toml               # Dependencies
```

## API Pattern

The API pattern groups code by HTTP resource:

```
my-api/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── users.py
│   │   │   └── posts.py
│   │   └── v2/
│   ├── models/
│   ├── schemas/
│   └── services/
├── public/                      # Static files
├── tests/
└── ...
```

## Layer Pattern

The layer pattern separates by technical concern:

```
my-api/
├── app/
│   ├── controllers/
│   ├── models/
│   ├── repositories/
│   ├── schemas/
│   └── services/
├── public/                      # Static files
├── tests/
└── ...
```

## Key Files

| File | Purpose |
|------|---------|
| `app/main.py` | Application factory, router mounting, static files |
| `app/core/config.py` | Pydantic settings, loads env file by `ENVIRONMENT` |
| `app/core/database.py` | SQLAlchemy engine and session |
| `public/` | Static files served at `/public` (HTML, images, CSS, JS) |
| `alembic.ini` | Database migration configuration |
| `.env` | Fallback environment variables (never commit!) |
| `.env.development` | Development environment settings |
| `.env.staging` | Staging environment settings |
| `.env.production` | Production environment settings |
