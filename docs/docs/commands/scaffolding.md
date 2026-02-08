---
sidebar_position: 2
---

# Scaffolding Commands

Generate application components quickly with make commands.

## Features

### make:feature

Create a complete feature module with all components.

```bash
fastman make:feature <name> [--crud]
```

| Option | Description |
|--------|-------------|
| `--crud` | Generate CRUD endpoints automatically |

```bash
# Basic feature
fastman make:feature product

# Feature with CRUD endpoints
fastman make:feature product --crud
```

**Creates:**
```
app/features/product/
├── __init__.py
├── models.py      # SQLAlchemy model
├── schemas.py     # Pydantic schemas
├── service.py     # Business logic
└── router.py      # API endpoints (with CRUD if --crud)
```

---

## Models & Schemas

### make:model

```bash
fastman make:model <name>
```

Creates a SQLAlchemy model file.

### make:schema

```bash
fastman make:schema <name>
```

Creates Pydantic request/response schemas.

---

## Services & Logic

### make:service

```bash
fastman make:service <name>
```

Creates a service class for business logic.

### make:repository

```bash
fastman make:repository <name>
```

Creates a repository pattern class for data access.

---

## HTTP Components

### make:controller

```bash
fastman make:controller <name>
```

Creates a controller class (for layer pattern).

### make:middleware

```bash
fastman make:middleware <name>
```

Creates HTTP middleware.

### make:dependency

```bash
fastman make:dependency <name>
```

Creates a FastAPI dependency.

---

## API & WebSocket

### make:api

```bash
fastman make:api <name> [--type=rest|graphql]
```

Creates REST or GraphQL API endpoints.

### make:websocket

```bash
fastman make:websocket <name>
```

Creates WebSocket feature with connection manager.

---

## Testing

### make:test

```bash
fastman make:test <name>
```

Creates a test file with pytest fixtures.

### make:factory

```bash
fastman make:factory <name>
```

Creates a model factory for generating test data.

---

## Database

### make:migration

```bash
fastman make:migration "<message>"
```

Creates an Alembic migration file.

### make:seeder

```bash
fastman make:seeder <name>
```

Creates a database seeder for initial/test data.

---

## Exceptions & Commands

### make:exception

```bash
fastman make:exception <name>
```

Creates a custom exception class with handler.

### make:command

```bash
fastman make:command <name>
```

Creates a custom CLI command.
