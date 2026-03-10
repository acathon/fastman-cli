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

Displays a table of all registered API routes. Supports filtering by path or HTTP method.

```bash
fastman route:list [--path=/api] [--method=GET]
```

**Options:**

- `--path`: Filter routes containing this path.
- `--method`: Filter by HTTP method (GET, POST, PUT, PATCH, DELETE).

---

## Authentication

### `install:auth`

Installs authentication scaffolding into your project.

```bash
fastman install:auth [--type=jwt|oauth|keycloak] [--provider=<provider>]
```

**Options:**

- `--type`: Auth type (default: `jwt`).
- `--provider`: Optional provider identifier for OAuth flows.

```bash
# JWT auth (default)
fastman install:auth

# Explicit type
fastman install:auth --type=keycloak
```

### `inspect`

Inspects a component of your application.

```bash
fastman inspect {type} {name}
```

- **Types**: `model`, `feature`, `api`.

### `optimize`

Optimizes the codebase by formatting and sorting imports. Will prompt to install missing tools.

```bash
fastman optimize [--check]
```

- Uses `black`, `isort`, and `autoflake`.
**Options:**

- `--check`: Only check for issues without modifying files.

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

Clears Python `__pycache__` directories and `.pyc` files. Handles permission errors gracefully.

```bash
fastman cache:clear
```

## Package Management

### `package:import`

Installs a Python package using the detected package manager (uv, poetry, pipenv, or pip).

```bash
fastman package:import {package_name}
```

### `package:list`

Lists installed packages.

```bash
fastman package:list
```

### `package:remove`

Removes a Python package.

```bash
fastman package:remove {package_name}
```

---

## CLI Helpers

### `list`

Lists all available Fastman commands.

```bash
fastman list
```

### `version`

Shows the installed Fastman version and environment info.

```bash
fastman version
```

### `docs`

Prints quick documentation links, or opens the docs site.

```bash
fastman docs [--open]
```

### `completion`

Generates shell completion scripts.

```bash
fastman completion <shell> [--install]
```

- **Shells**: `bash`, `zsh`, `fish`, `powershell`

### `activate`

Shows the activation command for an existing virtual environment in the current directory.

```bash
fastman activate [--create-script]
```
