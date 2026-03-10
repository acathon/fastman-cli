---
sidebar_position: 1
---

# Project Commands

Commands for creating, initializing, serving, and building FastAPI projects.

## `new`

Creates a brand-new FastAPI project with a complete directory structure, configuration files, database setup, migration tooling, and dependency management — all ready to run.

```bash
fastman new <project-name> [options]
```

### Options

| Option | Description | Default |
| --- | --- | --- |
| `--pattern` | Architecture pattern: `feature`, `api`, or `layer` | `feature` |
| `--database` | Database engine: `sqlite`, `postgresql`, `mysql`, `oracle`, `firebase` | `sqlite` |
| `--package` | Package manager: `uv`, `poetry`, `pipenv`, `pip` | auto-detected |
| `--minimal` | Skip optional dev dependencies (`faker`, `pytest`, `httpx`) | — |
| `--graphql` | Include GraphQL support with Strawberry (`app/core/graphql.py`) | — |

### Examples

```bash
# Simple project with defaults (feature pattern, SQLite, auto package manager)
fastman new my-api

# Production-ready with PostgreSQL and feature architecture
fastman new my-api --pattern=feature --database=postgresql

# Quick prototype with API versioning pattern
fastman new prototype --pattern=api --database=sqlite

# Firebase project (no SQL, no Alembic migrations)
fastman new mobile-backend --database=firebase

# Minimal project — smaller dependency footprint
fastman new tiny-api --minimal

# Include GraphQL support alongside REST
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

## `serve`

Starts the FastAPI development server using Uvicorn with hot-reload enabled by default. The server watches for file changes and automatically restarts.

```bash
fastman serve [options]
```

### Serve Options

| Option | Description | Default |
| --- | --- | --- |
| `--host` | Network interface to bind to | `127.0.0.1` |
| `--port` | Port number to listen on | `8000` |
| `--reload` | Explicitly enable hot reload (this is the default behavior) | `true` |
| `--no-reload` | Disable hot reload (for production-like testing) | — |

### Serve Examples

```bash
# Default — localhost:8000 with hot reload
fastman serve

# Custom port
fastman serve --port=3000

# Bind to all interfaces (accessible from other machines on the network)
fastman serve --host=0.0.0.0

# Production-like mode without reload
fastman serve --host=0.0.0.0 --no-reload
```

:::tip
Under the hood, Fastman runs `python -m uvicorn app.main:app` with the appropriate flags. This ensures it always works inside virtual environments, even when `uvicorn` isn't on your system PATH.
:::

---

## `init`

Initializes Fastman configuration in an existing FastAPI project. Use this when you have a project that wasn't created with `fastman new` but you want to use Fastman's commands.

```bash
fastman init
```

Creates the necessary directory structure (`app/core/`, `app/features/`, `app/console/commands/`) if they don't already exist.

---

## `build`

Prepares your project for production deployment. Can run tests, type checking, and optionally build a Docker image.

```bash
fastman build [--docker]
```

### Build Options

| Option | Description |
| --- | --- |
| `--docker` | Build a Docker image using the project's Dockerfile |

### Build Examples

```bash
# Standard build — runs pytest and mypy
fastman build

# Build and create a Docker image
fastman build --docker
```
