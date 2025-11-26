---
sidebar_position: 1
---

# Scaffolding Commands

Fastman provides a comprehensive suite of commands to generate boilerplate code instantly.

## Feature & API

### `make:feature`

Creates a new Vertical Slice feature.

```bash
fastman make:feature {name} [--crud]
```

- **Arguments**:
    - `name`: Name of the feature (e.g., `pizza`, `auth`).
- **Options**:
    - `--crud`: Generates Router, Service, Model, and Schema with full CRUD operations.

### `make:api`

Creates a lightweight API endpoint.

```bash
fastman make:api {name} [--style=rest|graphql]
```

- **Options**:
    - `--style`: `rest` (default) or `graphql`.

### `make:websocket`

Creates a WebSocket endpoint with a connection manager.

```bash
fastman make:websocket {name}
```

## Components

### `make:model`

Creates a SQLAlchemy model.

```bash
fastman make:model {name} [--table=tablename]
```

### `make:service`

Creates a Service class for business logic.

```bash
fastman make:service {name}
```

### `make:controller`

Creates a Controller class (for Layered architecture).

```bash
fastman make:controller {name}
```

### `make:repository`

Creates a Repository class for data access.

```bash
fastman make:repository {name}
```

### `make:middleware`

Creates a standard HTTP middleware.

```bash
fastman make:middleware {name}
```

### `make:dependency`

Creates a FastAPI dependency function or class.

```bash
fastman make:dependency {name}
```

### `make:exception`

Creates a custom exception class with standard HTTP error handling.

```bash
fastman make:exception {name}
```

## Testing & Seeding

### `make:test`

Creates a pytest file for a feature or unit.

```bash
fastman make:test {name}
```

### `make:seeder`

Creates a database seeder class.

```bash
fastman make:seeder {name}
```

### `make:factory`

Creates a model factory for generating test data.

```bash
fastman make:factory {name}
```

## System

### `make:command`

Creates a custom CLI command for your application.

```bash
fastman make:command {name}
```
