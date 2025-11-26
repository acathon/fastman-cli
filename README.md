# Fastman The Complete FastAPI CLI Framework

![Fastman Logo](docs/static/img/fastman-logo.png)

Fastman is a Laravel-inspired CLI tool for FastAPI. It eliminates boilerplate fatigue by generating project structures, handling database migrations, and scaffolding features, models, and middleware instantly.

Whether you prefer Vertical Slice (Feature) architecture or Layered architecture, Fastman sets it up for you in seconds.

## Features

- **Zero-Dependency Core**: Runs with standard library (Rich/Pyfiglet optional for UI).
- **Smart Package Detection**: Automatically uses uv, poetry, pipenv, or pip.
- **Multiple Architectures**: Supports feature (default), api, and layer patterns.
- **Database Ready**: First-class support for SQLite, PostgreSQL, MySQL, Oracle, and Firebase.
- **Interactive Shell**: Includes a tinker command to interact with your app context.
- **Auth Scaffolding**: One-command JWT or Keycloak authentication setup.

## Quick Start

### Installation

Make the script executable and available in your path (assuming you have cli.py):

```bash
# Rename to fastman and make executable
mv cli.py fastman
chmod +x fastman

# Move to a bin directory (optional)
sudo mv fastman /usr/local/bin/
```

### Create a New Project

Generate a new API with a specific architecture and package manager:

```bash
# Default (Feature pattern + UV + SQLite)
fastman new my-project

# Layered architecture with PostgreSQL and Poetry
fastman new blog_api --pattern=layer --database=postgresql --package=poetry
```

### Run the Server

```bash
cd my-project
fastman serve
```

## Project Architectures

Fastman supports three directory structures out of the box:

### 1. Feature Pattern (Default)
Best for domain-driven design and vertical slices. Code is organized by "what it does" rather than "what it is."

```plaintext
app/
├── features/
│   └── auth/           # Router, Service, Models, Schemas all in one place
├── api/                # Simple endpoints
└── core/               # Shared config
```

### 2. Layer Pattern
Traditional MVC-style architecture.

```plaintext
app/
├── controllers/
├── services/
├── repositories/
├── models/
└── schemas/
```

### 3. API Pattern
Lightweight structure for simple microservices.

```plaintext
app/
├── api/
├── schemas/
└── models/
```

## Command Reference

### Scaffolding
Generate boilerplate code instantly.

| Command | Description |
|---------|-------------|
| `make:feature {name} --crud` | Create a vertical slice (Router, Service, Model, Schema) |
| `make:model {name}` | Create a SQLAlchemy model |
| `make:api {name}` | Create a lightweight REST or GraphQL endpoint |
| `make:service {name}` | Create a business logic service class |
| `make:repository {name}` | Create a repository data-access class |
| `make:middleware {name}` | Create a standard HTTP middleware |
| `make:dependency {name}` | Create a FastAPI dependency function/class |
| `make:websocket {name}` | Create a WebSocket endpoint with connection manager |
| `make:test {name}` | Create a pytest file |
| `make:seeder {name}` | Create a database seeder |
| `make:factory {name}` | Create a model factory for testing |

### Database & Migrations
Wrappers around Alembic to make migrations feel like Laravel.

| Command | Description |
|---------|-------------|
| `make:migration {msg}` | Create a new migration file |
| `migrate` | Run pending migrations |
| `migrate:rollback` | Rollback the last migration |
| `migrate:reset` | Rollback all migrations |
| `db:seed` | Run database seeders |

### Utilities

| Command | Description |
|---------|-------------|
| `tinker` | Interactive Python Shell with app context loaded |
| `route:list` | Show a table of all registered API routes |
| `serve` | Start the development server (Uvicorn wrapper) |
| `install:auth` | Scaffold JWT, OAuth, or Keycloak authentication |
| `inspect {type} {name}` | Inspect a model, feature, or API |
| `optimize` | Format code, sort imports, and remove unused variables |

## The "Tinker" Shell

Debugging FastAPI apps can be tedious. Fastman includes a tinker command that drops you into a shell with your settings, db session, and models pre-loaded.

```bash
$ fastman tinker

Fastman Interactive Shell
Available: settings, SessionLocal, Base, db

>>> user = db.query(User).first()
>>> print(user.email)
admin@example.com
>>> settings.DEBUG
True
```

## Authentication

Don't write auth from scratch. Scaffold it:

```bash
fastman install:auth --type=jwt
```

This generates:
- `app/features/auth/` (Router, Service, Schemas)
- JWT handling utilities
- User model and migration
- Login/Register endpoints

## License

This project is licensed under the **Apache License 2.0**.
