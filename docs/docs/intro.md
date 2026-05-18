---
sidebar_position: 1
---

# Fastman

**The elegant CLI for FastAPI developers.**

Fastman is an opinionated, batteries-included command-line tool that brings structure, speed, and best practices to FastAPI development. Instead of manually wiring up project scaffolding, database configurations, migrations, and authentication — Fastman handles it all from the terminal so you can focus on building your application logic.

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
| **`install:cert`** | Build a merged CA bundle from project-local `.pem` / `.crt` files for private services |
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

## What's New in v0.4.2 (Dolphin)

- **`route:list --json`** — machine-readable route export, ready to pipe into `jq` or feed into CI scripts that verify expected routes.
- **`db:fresh`** — one-shot "wipe + migrate + (optional) seed" for the common dev-reset loop. Refuses to run when `ENVIRONMENT=production` as a safety net.
- **`model:show <name>`** — SQLAlchemy model introspection that walks every model module, finds the named class (snake/Pascal-case tolerant), and renders columns / relationships / indexes as Rich tables. Replaces the `inspect` command dropped in v0.4.0.

## What's New in v0.4.1 (Dolphin)

- **`fastman update`** — re-scaffold drifted project files against current templates. Diff each fastman-owned file (database.py, config.py, alembic/env.py, mail/, auth/) against what fastman would generate today; pick keep/update per file. Closes the mid-project lifecycle gap: pull in SQLAlchemy 2.0, Pydantic v2, dropped `.env.production`, etc. without recreating your project. Supports `--check` for CI and `--all` for unattended runs.
- **AST-aware code injection** — `install:auth --type=keycloak` and `install:mail` no longer rely on fragile `str.replace()` on hardcoded anchor strings. Both now parse `app/main.py` and `app/core/config.py` with `ast` to locate the target class structurally, wrap injected blocks in `# fastman:<tag>:start` / `:end` markers for idempotent re-runs, and `ast.parse()` the result to guarantee the file still compiles. No more silent no-ops when you've customized a comment.

## What's New in v0.4.0 (Dolphin)

- **Lean command surface** — 6 low-leverage commands removed (`package:list`, `config:cache/clear`, `inspect`, `migrate:reset`, `package:import` → `package:install`). Use the underlying tool directly or the renamed equivalent.
- **Mail scaffolding** — new `install:mail` (SMTP/SendGrid/Mailgun/SES) and `make:mail` commands with HTML or Markdown templates and FastAPI BackgroundTasks integration.
- **Modern codegen** — generated models use SQLAlchemy 2.0 `DeclarativeBase` + typed `Mapped[]` columns; schemas use Pydantic v2 `ConfigDict`.
- **Smart pluralization** — `address → addresses`, `category → categories`, `analysis → analyses`, `person → people`. No more `addresss` in your tablenames.
- **Pattern-aware `make:*`** — `.fastmanrc` records the project pattern; running `make:controller` in a feature-pattern project now gives an actionable error.
- **Keyword + builtin guard** — `fastman make:feature class` is rejected before any code is generated.
- **Dynamic shell completions** — bash / zsh / fish / powershell auto-include every registered command, with zero static lists to keep in sync.

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
