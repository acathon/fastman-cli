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

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--pattern` | Architecture pattern: `feature`, `api`, `layer` | `feature` |
| `--database` | Database: `sqlite`, `postgresql`, `mysql`, `oracle`, `firebase` | `sqlite` |
| `--package` | Package manager: `uv`, `poetry`, `pipenv`, `pip` | auto-detect |

### Examples

```bash
# Simple project with defaults
fastman new my-api

# Production-ready with PostgreSQL
fastman new my-api --pattern=feature --database=postgresql

# Quick prototype with API pattern
fastman new prototype --pattern=api --database=sqlite

# Firebase project (no Alembic)
fastman new mobile-backend --database=firebase
```

### What Gets Created

```
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

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--host` | Host to bind | `127.0.0.1` |
| `--port` | Port number | `8000` |
| `--reload` | Enable hot reload | `true` |
| `--no-reload` | Disable hot reload | — |

### Examples

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

### Options

| Option | Description |
|--------|-------------|
| `--docker` | Build Docker image |

### Examples

```bash
# Standard build
fastman build

# Docker build
fastman build --docker
```
