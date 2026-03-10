---
sidebar_position: 2
---

# Scaffolding Commands

Fastman's `make:*` commands generate boilerplate code for every component type in your application. Each command creates properly structured files with correct imports, type hints, and naming conventions — so you can start writing business logic immediately.

All generated code follows the architecture pattern you chose when creating the project (feature, api, or layer).

## Features

### `make:feature`

The most powerful scaffolding command. Creates a complete **vertical slice** — a self-contained feature module with a model, Pydantic schemas, service layer, and router. This is the recommended way to add new functionality to a feature-pattern project.

```bash
fastman make:feature <name> [--crud]
```

| Option | Description |
| --- | --- |
| `--crud` | Generate CRUD endpoints automatically |

```bash
# Basic feature
fastman make:feature product

# Feature with CRUD endpoints
fastman make:feature product --crud
```

**Creates:**

```text
app/features/product/
├── __init__.py
├── models.py      # SQLAlchemy model
├── schemas.py     # Pydantic schemas
├── service.py     # Business logic
└── router.py      # API endpoints (with CRUD if --crud)
```

---

## Models & Schemas

### `make:model`

Creates a SQLAlchemy model file with standard columns (`id`, `created_at`, `updated_at`) and a configurable table name.

```bash
fastman make:model <name> [--table=<table_name>]
```

| Option | Description |
| --- | --- |
| `--table` | Override the auto-generated table name (defaults to the pluralized snake_case name) |

### `make:schema`

Creates Pydantic schema classes for request validation and response serialization. Generates `Base`, `Create`, `Update`, and `Response` variants.

```bash
fastman make:schema <name>
```

---

## Services & Logic

### `make:service`

Creates a service class for encapsulating business logic. Services are the recommended layer for operations that involve validation, data transformation, or coordination between multiple models.

```bash
fastman make:service <name>
```

### `make:repository`

Creates a repository class that abstracts database access behind a clean interface. Useful in the layer pattern for separating query logic from business logic.

```bash
fastman make:repository <name>
```

---

## HTTP Components

### `make:controller`

Creates a controller class for the **layer pattern** only. If you're using the feature pattern, use `make:feature` instead.

```bash
fastman make:controller <name>
```

### `make:middleware`

Creates an HTTP middleware class that can intercept requests and responses. Common uses include logging, rate limiting, CORS, and request validation.

```bash
fastman make:middleware <name>
```

### `make:dependency`

Creates a FastAPI dependency — a reusable injectable function or class. Dependencies are FastAPI's built-in mechanism for shared logic like authentication, database sessions, and pagination.

```bash
fastman make:dependency <name>
```

---

## API & WebSocket

### `make:api`

Creates REST or GraphQL API endpoints in the `app/api/` directory. For REST, generates a router with standard CRUD endpoints. For GraphQL, generates a Strawberry schema with queries and mutations.

```bash
fastman make:api <name> [--style=rest|graphql]
```

| Option | Description | Default |
| --- | --- | --- |
| `--style` | API style: `rest` for RESTful endpoints, `graphql` for Strawberry GraphQL | `rest` |

### `make:websocket`

Creates a WebSocket feature with a connection manager class and WebSocket router. The generated manager handles connection tracking, personal messages, and broadcasting.

```bash
fastman make:websocket <name>
```

---

## Testing

### `make:test`

Creates a test file with pytest fixtures and a basic test structure. The generated file includes an async client fixture and example test cases.

```bash
fastman make:test <name>
```

### `make:factory`

Creates a model factory that uses [Faker](https://faker.readthedocs.io/) to generate realistic test data. Factories provide `make()` (returns a dict) and `create()` (persists to database) methods.

```bash
fastman make:factory <name>
```

---

## Database

### `make:migration`

Creates an Alembic migration file. The message becomes the migration filename and revision description.

```bash
fastman make:migration "<message>"
```

```bash
fastman make:migration "create users table"
fastman make:migration "add email index to posts"
```

### `make:seeder`

Creates a database seeder class for populating your database with initial or test data. Seeders are stored in `database/seeders/`.

```bash
fastman make:seeder <name>
```

---

## Exceptions & Commands

### `make:exception`

Creates a custom exception class with a FastAPI exception handler. The handler automatically returns a properly formatted JSON error response.

```bash
fastman make:exception <name>
```

### `make:command`

Creates a custom CLI command that extends Fastman. Your command is automatically discovered and available via `fastman <your-command>`. See the [Custom Commands](../advanced/custom-commands) guide for details.

```bash
fastman make:command <name>
```
