---
sidebar_position: 1
---

# Fastman

**The elegant CLI for FastAPI artisans.**

Fastman is a Laravel-inspired command-line tool that brings structure, speed, and best practices to FastAPI development. Instead of manually wiring up project scaffolding, database configurations, migrations, and authentication — Fastman handles it all from the terminal so you can focus on building your application logic.

## 30 seconds to your first API

```bash
# 1. Install
pip install fastman

# 2. Create a project with PostgreSQL
fastman create my-api --database=postgresql

# 3. Navigate into the project and scaffold a feature
cd my-api
fastman make:feature users --crud

# 4. Create a migration, apply it, and start the server
fastman make:migration "create users table"
fastman database:migrate
fastman serve
```

Open **http://localhost:8000/docs** — you now have a fully documented REST API with CRUD endpoints, Swagger UI, database migrations, and a clean project structure.

## Why Fastman?

FastAPI gives you incredible performance and flexibility — but every new project means repeating the same setup: choosing an architecture, configuring a database connection, setting up Alembic for migrations, adding authentication, and writing boilerplate for every new feature.

**Fastman eliminates that repetitive work.** With a single command you get opinionated defaults that follow production-tested best practices, while every generated file remains fully customizable. There's no lock-in — it's your code from the start.

## What you get

| Command | What it does |
|---|---|
| **`fastman create`** | Production-ready project with configuration, database, migrations, and tests |
| **`make:feature`** | Complete vertical slice — model, schema, service, and router — in one command |
| **`make:model`, `make:service`, ...** | 15+ generators for every component type (controllers, middleware, repos, etc.) |
| **`database:migrate`** | Alembic migrations without touching INI files or configuration |
| **`install:auth --type=jwt`** | Full JWT auth with `/register`, `/login`, `/me` endpoints and password hashing |
| **`install:certificate`** | Trust project-local `.pem` / `.crt` files from `certs/` for private services |
| **`serve`** | Development server with automatic hot reload |
| **`tinker`** | Interactive Python shell with your database session pre-loaded |
| **`route:list`** | View all registered API routes in a formatted table |

### Supported databases

SQLite · PostgreSQL · MySQL · Oracle · Firebase

### Supported package managers

uv · poetry · pipenv · pip — auto-detected from your project

### Architecture patterns

- **Feature** — vertical slices, each feature is self-contained (recommended)
- **API** — resource-grouped with built-in API versioning
- **Layer** — traditional MVC-style separation of concerns

## What's New in v0.3.5 (Cheetah)

- Keycloak switched to [`fastapi-keycloak`](https://github.com/fastapi-keycloak/fastapi-keycloak) with dependency-based route protection
- `GET /me` endpoint automatically registered for Keycloak auth
- Swagger Authorize button via `idp.add_swagger_config(app)`
- User, role, and group management through the `FastAPIKeycloak` instance

See the full [changelog](./whats-new).

---

<div className="row">
  <div className="col col--6">
    <h3>📖 Getting Started</h3>
    <p>New to Fastman? Start here — install the CLI and create your first project in under 5 minutes.</p>
    <a href="/fastman-cli/docs/installation">Installation →</a>
  </div>
  <div className="col col--6">
    <h3>🎯 Commands Reference</h3>
    <p>Browse all 30+ commands with options, flags, and real-world examples.</p>
    <a href="/fastman-cli/docs/commands/project">View Commands →</a>
  </div>
</div>
