# Fastman CLI

![Fastman Logo](docs/assets/fastman-logo.jpg)


The CLI for Python FastAPI.

Fastman is a powerful command-line interface designed to streamline FastAPI development. It provides a suite of scaffolding commands to generate project structures, features, APIs, database models, and more, inspired by modern frameworks.

## Features

- **Project Scaffolding**: Create new FastAPI projects with a robust, production-ready structure.
- **Vertical Slice Architecture**: Generate features with routers, services, models, and schemas in one go.
- **Database Management**: Commands for migrations (Alembic), seeders, factories, and models.
- **Authentication**: One-command installation for JWT or Keycloak authentication.
- **Package Management**: Smart wrapper around `uv`, `poetry`, or `pip`.
- **Development Tools**: Built-in server, interactive shell (tinker), and route listing.

## Installation

Fastman is a dependency-free CLI tool (only requires standard library + `pyfiglet` for banner).

```bash
# Install from PyPI
pip install fastman

# Or install locally
git clone https://github.com/acathon/fastman-cli.git
cd fastman-cli
pip install .
```

> **Note:** Ensure your Python scripts directory is in your PATH to use the `fastman` command directly.


## Usage

### Creating a New Project

```bash
fastman new my-project
cd my-project
```

This will create a new directory `my-project` with a complete FastAPI application structure, including:
- `app/core`: Configuration, database, security.
- `app/features`: Vertical slice features.
- `app/api`: Light endpoints.
- `tests`: Test structure.
- `alembic`: Database migrations.

### Scaffolding Commands

**Features & APIs:**
```bash
fastman make:feature user      # Creates app/features/user (Router, Service, Model, Schema)
fastman make:api items         # Creates app/api/items (Simple Endpoint)
fastman make:websocket chat    # Creates WebSocket endpoint
```

**Database:**
```bash
fastman make:model Product     # Creates app/models/product.py
fastman make:migration "init"  # Creates Alembic migration
fastman migrate                # Runs migrations
fastman make:seeder User       # Creates database seeder
fastman db:seed                # Runs seeders
```

**Core Components:**
```bash
fastman make:controller Auth   # Creates MVC Controller
fastman make:service Payment   # Creates Service class
fastman make:middleware Log    # Creates Middleware
fastman make:exception Custom  # Creates Custom Exception
```

### Development

```bash
fastman serve       # Starts the development server (Uvicorn)
fastman tinker      # Starts an interactive shell with app context
fastman route:list  # Lists all registered API routes
```

## Project Structure

Fastman encourages a clean, modular architecture:

```
app/
├── api/            # Simple, single-file endpoints
├── console/        # Custom console commands
├── core/           # Core config, DB, auth, middleware
├── features/       # Vertical slice features (domain-driven)
├── http/           # MVC Controllers (optional)
├── models/         # Database models
├── services/       # Business logic services
└── main.py         # App entry point
```

## License

MIT
