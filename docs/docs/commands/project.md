---
sidebar_position: 4
---

# Project Commands

Commands for creating, initializing, and building Fastman projects.

## `new`

The `new` command is the starting point for any Fastman application. It scaffolds a complete, production-ready directory structure configured with your preferred tools and architecture.

```bash
fastman new {name} [options]
```

### Arguments

- **`name`** (Required): The name of your project. This will create a directory with this name and set it as the project name in `pyproject.toml`.

### Options

#### `--pattern`
Defines the architectural style of the generated project.

- **`feature`** (Default): **Vertical Slice Architecture**.
    - Best for: Medium to large applications, domain-driven design.
    - Structure: Code is organized by "features" (e.g., `auth`, `billing`, `users`), where each feature contains its own models, schemas, services, and routes.
    - **Why use it?** Keeps related code together, making it easier to scale and maintain as the team grows.

- **`layer`**: **Layered (MVC) Architecture**.
    - Best for: Traditional web apps, teams familiar with Django/Laravel/Spring.
    - Structure: Code is organized by technical layer (`controllers`, `models`, `services`, `repositories`).
    - **Why use it?** Familiar separation of concerns. Good for smaller projects or strict technical separation.

- **`api`**: **Minimal API**.
    - Best for: Microservices, simple endpoints, prototypes.
    - Structure: Flat structure with a single `main.py` or simple `api` folder.
    - **Why use it?** Low overhead, maximum speed for simple tasks.

#### `--database`
Configures the database connection, drivers, and initial migration setup.

- **`sqlite`** (Default):
    - Sets up `sqlite:///./sql_app.db`.
    - Great for development and testing. No external server required.
- **`postgresql`**:
    - Installs `psycopg2-binary`.
    - Configures `.env` for Postgres connection.
    - Production standard.
- **`mysql`**:
    - Installs `mysqlclient`.
    - Configures `.env` for MySQL/MariaDB.
- **`oracle`**:
    - Installs `cx_Oracle`.
    - Enterprise grade setup.
- **`firebase`**:
    - Sets up Firebase Admin SDK.
    - Good for NoSQL/Real-time apps.

#### `--package`
Selects the Python package manager to initialize the project with.

- **`uv`** (Default):
    - The fastest option. Uses `uv` for lightning-fast installs and dependency resolution.
    - **Highly Recommended**.
- **`poetry`**:
    - Uses `poetry` for dependency management.
    - Robust, standard for many Python teams.
- **`pipenv`**:
    - Uses `Pipfile` and `pipenv`.
- **`pip`**:
    - Standard `requirements.txt` and `venv`.
    - Simple, no extra tools required.

#### `--minimal`
Skips the creation of optional directories and files (like `tests`, `scripts`, etc.) for a cleaner start.

### Examples

**Standard Project (Recommended)**
```bash
fastman new my-app
```
*Creates a Vertical Slice app with SQLite and uv.*

**Production Ready Stack**
```bash
fastman new enterprise-app --pattern=feature --database=postgresql --package=poetry
```
*Creates a robust feature-based app with Postgres and Poetry.*

**Microservice**
```bash
fastman new payment-service --pattern=api --minimal
```
*Creates a lightweight API service.*

---

## `init`

Initializes Fastman in an existing project directory.

```bash
fastman init
```

This command is useful if you have an existing FastAPI project and want to start using Fastman's CLI tools (like `make:controller` or `migrate`). It will:
1. Create the `.fastman` configuration.
2. Scaffold necessary directories (`app/console`, `app/core`).
3. Set up the base `Command` structure.

---

## `build`

Builds the project for production.

```bash
fastman build [--docker]
```

### Options

- **`--docker`**: Automatically generates a `Dockerfile` and builds a Docker image for your application.
    - The generated Dockerfile is optimized for size and security (using `python:slim`).
    - It includes build steps for your chosen package manager.

- **Default (no flags)**:

- **`--open`**: Automatically opens `https://fastman.dev/docs` in your default browser.

---

## `version`

Shows version information.

```bash
fastman version
```
