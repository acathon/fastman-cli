---
sidebar_position: 3
---

# Utility Commands

Commands for development workflow, configuration management, package management, and general CLI helpers.

## Development Tools

### `tinker`

Starts an interactive Python shell (REPL) with your application context pre-loaded. This is invaluable for debugging, quick data exploration, and testing queries without writing a script.

```bash
fastman tinker
```

When you enter tinker, the following are automatically available:
- `db` — an active SQLAlchemy database session
- `settings` — your `app/core/config.py` settings object
- `Base` — the SQLAlchemy declarative base

If [IPython](https://ipython.org/) is installed, tinker uses it automatically for syntax highlighting, tab completion, and magic commands. Otherwise, it falls back to Python's built-in REPL.

```bash
# Install IPython for the best tinker experience
pip install ipython
```

See the full [Tinker guide](../advanced/tinker) for tips and tricks.

### `route:list`

Displays a formatted table of all registered API routes in your application. Useful for verifying endpoint registration and debugging routing issues.

```bash
fastman route:list [--path=/api] [--method=GET]
```

| Option | Description |
|--------|-------------|
| `--path` | Filter routes that contain this path segment (e.g., `/api/v1`) |
| `--method` | Filter by HTTP method: `GET`, `POST`, `PUT`, `PATCH`, `DELETE` |

```bash
# Show all routes
fastman route:list

# Only GET endpoints
fastman route:list --method=GET

# Only routes under /users
fastman route:list --path=/users
```

### `inspect`

Inspects a component of your application and displays its structure.

```bash
fastman inspect {type} {name}
```

| Argument | Description |
|----------|-------------|
| `type` | What to inspect: `model`, `feature`, or `api` |
| `name` | The name of the component to inspect |

```bash
# Inspect a model's columns and types
fastman inspect model user

# Inspect a feature module's files
fastman inspect feature product
```

### `optimize`

Formats your codebase using `black`, sorts imports with `isort`, and removes unused imports with `autoflake`. If any of these tools are missing, Fastman will offer to install them.

```bash
fastman optimize [--check]
```

| Option | Description |
|--------|-------------|
| `--check` | Only check for issues without modifying files (useful in CI pipelines) |

---

## Authentication

### `install:auth`

Scaffolds a complete authentication system into your project. Creates models, schemas, security utilities, service layer, dependencies, and router endpoints.

```bash
fastman install:auth [--type=jwt|oauth|keycloak] [--provider=<provider>]
```

| Option | Description | Default |
|--------|-------------|---------|
| `--type` | Authentication strategy: `jwt`, `oauth`, or `keycloak` | `jwt` |
| `--provider` | OAuth provider identifier (only used with `--type=oauth`) | — |

```bash
# JWT authentication (default) — creates /register, /login, /me endpoints
fastman install:auth

# Explicit JWT
fastman install:auth --type=jwt

# Keycloak enterprise SSO
fastman install:auth --type=keycloak

# OAuth with Google
fastman install:auth --type=oauth --provider=google
```

:::info OAuth note
The OAuth scaffolding installs `authlib` and `httpx` as dependencies but requires manual configuration for your specific OAuth provider (client ID, client secret, callback URL). See the [Authentication concepts](../concepts/authentication) page for details.
:::

---

## Configuration

### `generate:key`

Generates a cryptographically secure `SECRET_KEY` using `secrets.token_urlsafe()` and writes it to **all** environment files (`.env`, `.env.development`, `.env.staging`, `.env.production`).

```bash
fastman generate:key [--show]
```

| Option | Description |
|--------|-------------|
| `--show` | Print the generated key to the terminal without writing to files |

### `config:cache`

Caches your environment configuration to `config_cache.json` for faster startup in production. Reads from the environment-specific file based on the `ENVIRONMENT` variable (defaults to `.env.development`, falls back to `.env`).

```bash
fastman config:cache

# Cache staging config
ENVIRONMENT=staging fastman config:cache
```

### `config:clear`

Removes the cached configuration file so the application reads from `.env` again.

```bash
fastman config:clear
```

### `cache:clear`

Recursively removes all `__pycache__` directories and `.pyc` files from your project. Handles permission errors gracefully.

```bash
fastman cache:clear
```

---

## Package Management

Fastman automatically detects your package manager (uv, poetry, pipenv, or pip) and uses it for all package operations.

### `package:import`

Installs a Python package using your detected package manager.

```bash
fastman package:import {package_name}
```

```bash
fastman package:import requests
fastman package:import "sqlalchemy>=2.0"
```

### `package:list`

Lists all installed packages in the current environment.

```bash
fastman package:list
```

### `package:remove`

Uninstalls a Python package.

```bash
fastman package:remove {package_name}
```

---

## CLI Helpers

### `list`

Shows all available Fastman commands grouped by category.

```bash
fastman list
```

### `version`

Displays the installed Fastman version, Python version, and detected package manager.

```bash
fastman version
```

### `docs`

Prints quick-reference documentation links, or opens the documentation site in your default browser.

```bash
fastman docs [--open]
```

| Option | Description |
|--------|-------------|
| `--open` | Open the documentation website in your browser |

### `completion`

Generates shell completion scripts for tab-completing Fastman commands and options.

```bash
fastman completion <shell> [--install]
```

| Argument/Option | Description |
|--------|-------------|
| `shell` | Target shell: `bash`, `zsh`, `fish`, or `powershell` |
| `--install` | Install the completion script to the appropriate shell config file |

```bash
# Print the bash completion script
fastman completion bash

# Install fish completions directly
fastman completion fish --install
```

### `activate`

Prints the activation command for the virtual environment in the current directory. Useful if you forget the platform-specific syntax.

```bash
fastman activate [--create-script]
```

| Option | Description |
|--------|-------------|
| `--create-script` | Create a helper script (`activate.sh` or `activate.bat`) in the project directory |

```bash
$ fastman activate
# Linux/macOS:  source .venv/bin/activate
# Windows:      .\.venv\Scripts\activate
```
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
