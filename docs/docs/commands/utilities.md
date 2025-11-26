---
sidebar_position: 3
---

# Utility Commands

Helper commands to manage your application, configuration, and environment.

## Development

### `tinker`

Starts an interactive Python shell with the application context loaded.

```bash
fastman tinker
```

**Features**:
- Pre-loaded `db` session.
- Access to `settings` and `Base` models.
- Uses `IPython` if available.

### `route:list`

Displays a table of all registered API routes.

```bash
fastman route:list [--path=/api] [--method=GET]
```

### `inspect`

Inspects a component of your application.

```bash
fastman inspect {type} {name}
```

- **Types**: `model`, `feature`, `api`.

### `optimize`

Optimizes the codebase by formatting and sorting imports.

```bash
fastman optimize [--check]
```

- Uses `black`, `isort`, and `autoflake`.

## Configuration

### `generate:key`

Generates a new `SECRET_KEY` and updates `.env`.

```bash
fastman generate:key [--show]
```

### `config:cache`

Caches environment variables to `config_cache.json` for faster loading in production.

```bash
fastman config:cache
```

### `config:clear`

Clears the configuration cache.

```bash
fastman config:clear
```

### `cache:clear`

Clears Python `__pycache__` and `.pyc` files.

```bash
fastman cache:clear
```

## Package Management

### `import`

Installs a Python package using the detected package manager.

```bash
fastman import {package_name}
```

### `pkg:list`

Lists installed packages.

```bash
fastman pkg:list
```
