---
sidebar_position: 1
---

# Project Commands

Commands for creating and managing FastAPI projects.

## new

Create a new FastAPI project with a complete scaffold.

```bash
fastman new <project-name> [options]
```

### New Options

| Option | Description | Default |
| --- | --- | --- |
| `--minimal` | Create a minimal project (skips optional dev dependencies) | — |
| `--pattern` | Architecture pattern: `feature`, `api`, `layer` | `feature` |
| `--database` | Database: `sqlite`, `postgresql`, `mysql`, `oracle`, `firebase` | `sqlite` |
| `--package` | Package manager: `uv`, `poetry`, `pipenv`, `pip` | `uv` |
| `--graphql` | Include GraphQL support (adds `app/core/graphql.py`) | — |

### New Examples

```bash
# Simple project with defaults
fastman new my-api

# Production-ready with PostgreSQL
fastman new my-api --pattern=feature --database=postgresql

# Quick prototype with API pattern
fastman new prototype --pattern=api --database=sqlite

# Firebase project (no Alembic)
fastman new mobile-backend --database=firebase

# Minimal project (smaller dependency set)
fastman new tiny-api --minimal

# Include GraphQL support
fastman new gql-api --graphql
```

### What Gets Created

```text
my-api/
├── app/
│   ├── core/
│   │   ├── config.py          # Pydantic settings
│   │   ├── database.py        # SQLAlchemy setup
│   │   └── dependencies.py    # Common dependencies
│   ├── features/              # Your feature modules
│   └── main.py               # App entry point
├── database/
│   ├── migrations/           # Alembic migrations
│   └── seeders/              # Database seeders
├── tests/                    # Test directory
├── .env                      # Environment variables
├── .gitignore
├── alembic.ini              # Migration config
├── pyproject.toml           # Dependencies
└── README.md
```

---

## serve

Start the development server.

```bash
fastman serve [options]
```

### Serve Options

| Option | Description | Default |
| --- | --- | --- |
| `--host` | Host to bind | `127.0.0.1` |
| `--port` | Port number | `8000` |
| `--reload` | Enable hot reload (default behavior) | `true` |
| `--no-reload` | Disable hot reload | — |

### Serve Examples

```bash
# Default (localhost:8000 with reload)
fastman serve

# Custom port
fastman serve --port=3000

# Production-like (no reload)
fastman serve --host=0.0.0.0 --no-reload
```

---

## init

Initialize Fastman in an existing project.

```bash
fastman init
```

Creates configuration files if missing.

---

## build

Build the project for production.

```bash
fastman build [--docker]
```

### Build Options

| Option | Description |
| --- | --- |
| `--docker` | Build Docker image |

### Build Examples

```bash
# Standard build
fastman build

# Docker build
fastman build --docker
```
