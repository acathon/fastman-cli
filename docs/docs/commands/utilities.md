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

Fastman includes [IPython](https://ipython.org/) by default, so tinker opens with syntax highlighting, tab completion, and magic commands out of the box. If IPython cannot be imported for any reason, it falls back to Python's built-in REPL.

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

### `env`

Shows the active environment file, its variables, and certificate paths. When used with `--source`, it persistently switches the environment for all future `fastman serve` calls.

```bash
fastman env [--source=development|staging|production] [--reset]
```

| Option | Description |
|--------|-------------|
| `--source` | Set and lock the active environment file (`develop` or `staging`) |
| `--reset` | Clear the locked selection and return to auto-detect |

```bash
# Show current active environment, variables, and cert paths
fastman env

# Lock to .env.develop — serve will use it automatically
fastman env --source=develop

# Lock to .env.staging
fastman env --source=staging

# Clear the lock, return to auto-detect (.env.develop > .env)
fastman env --reset
```

Resolution priority for `fastman serve`:
1. `--env=X` flag (always overrides)
2. `.fastmanrc` lock (set by `fastman env --source=`)
3. `.env.develop` (auto-detect default)
4. `.env` (fallback)

:::tip
`.fastmanrc` is added to the generated `.gitignore` by default — it stores per-developer state (locked env) alongside the recorded project shape.
:::

### `optimize`

Formats and lints your codebase using `ruff` (which replaced `black`/`isort`/`autoflake` in 0.3.x). If `ruff` is missing, Fastman will offer to install it.

```bash
fastman optimize [--check]
```

| Option | Description |
|--------|-------------|
| `--check` | Only check for issues without modifying files (useful in CI pipelines) |

---

## Third-Party Integrations

### `install:auth`

Scaffolds a complete authentication system into your project. Creates models, schemas, security utilities, service layer, dependencies, and router endpoints.

```bash
fastman install:auth [--type=jwt|oauth|keycloak|passkey] [--provider=<provider>] [--append-certificate]
```

| Option | Description | Default |
|--------|-------------|---------|
| `--type` | Authentication strategy: `jwt`, `oauth`, `keycloak`, or `passkey` | `jwt` |
| `--provider` | OAuth provider identifier (only used with `--type=oauth`) | — |
| `--append-certificate` | Prepare a merged CA bundle from `certs/` and wire env vars after Keycloak installation | disabled |

```bash
# JWT authentication (default) — creates /register, /login, /me endpoints
fastman install:auth

# Explicit JWT
fastman install:auth --type=jwt

# Keycloak enterprise SSO
fastman install:auth --type=keycloak

# Keycloak with project certificates prepared as a merged CA bundle
fastman install:auth --type=keycloak --append-certificate

# OAuth with Google
fastman install:auth --type=oauth --provider=google

# Passkey / WebAuthn
fastman install:auth --type=passkey
```

:::info OAuth note
The OAuth scaffolding installs `authlib` and `httpx` as dependencies but requires manual configuration for your specific OAuth provider (client ID, client secret, callback URL). See the [Authentication concepts](../concepts/authentication) page for details.
:::

:::tip Keycloak certificates
Place `.pem` or `.crt` files in your project's `certs/` directory before using `--append-certificate`. Fastman builds a merged CA bundle and writes `CERTS_PATH`, `REQUESTS_CA_BUNDLE`, and `SSL_CERT_FILE` into your env files so HTTP clients can trust internal or private certificate chains.
:::

### `install:cert`

Builds `certs/ca-bundle-merged.pem` from the system `certifi` bundle plus your project's `.pem` / `.crt` files. It also writes `CERTS_PATH`, `REQUESTS_CA_BUNDLE`, and `SSL_CERT_FILE` into your env files when needed. This is useful for Keycloak, internal gateways, tests, SDKs, and any third-party service that uses a private CA.

```bash
fastman install:cert
```

```bash
# Create certs/ if it does not exist, then add your certificate files
fastman install:cert

# After copying certificates into certs/, run again to rebuild the bundle
fastman install:cert
```

---

## Configuration

### `config:appkey`

Generates a cryptographically secure `SECRET_KEY` using `secrets.token_urlsafe()` and writes it to **all** environment files (`.env`, `.env.develop`, `.env.staging`).

```bash
fastman config:appkey [--show]
```

| Option | Description |
|--------|-------------|
| `--show` | Print the generated key to the terminal without writing to files |

### `cache:clear`

Recursively removes all `__pycache__` directories and `.pyc` files from your project. Handles permission errors gracefully.

```bash
fastman cache:clear
```

---

## Package Management

Fastman ships `package:install` and `package:remove` — thin wrappers that pick
the right backend (uv / poetry / pipenv / pip) automatically and, on **pip**,
install into the project's `.venv` even when the user hasn't activated it.

### `package:install`

```bash
fastman package:install requests
fastman package:install "sqlalchemy>=2.0"
```

What it does per backend:

| Backend detected | Underlying call | Where the install lands |
|------------------|-----------------|------------------------|
| uv (`uv.lock` present) | `uv add <pkg>` | Project's uv-managed env |
| poetry (`poetry.lock` present) | `poetry add <pkg>` | Project's poetry env |
| pipenv (`Pipfile` present) | `pipenv install <pkg>` | Project's pipenv env |
| pip (anything else) | `.venv/bin/pip install <pkg>` (or `.venv\Scripts\pip.exe` on Windows) | Project's `.venv` — **even when not activated** |

If no `.venv` / `venv` / `env` directory exists, fastman warns and falls back
to `python -m pip install`, which may write to a global site-packages
(create or activate a venv first to avoid this).

The pip backend also keeps `requirements.txt` in sync.

### `package:remove`

```bash
fastman package:remove requests
```

Mirror of `package:install`: dispatches to the right backend and prunes
`requirements.txt` on the pip backend.

### Why not just use the underlying tool?

If you're on uv / poetry / pipenv, calling those directly (`uv add X`,
`poetry add X`, `pipenv install X`) is equally fine — they already manage the
venv. The wrappers earn their keep mainly for the **pip** case, where bare
`pip install` can land in the wrong interpreter when the user has fastman
installed globally but hasn't activated their project's venv. Use whichever
is faster for you.

:::tip
Listing packages is one underscore away in every backend (`uv pip list`,
`poetry show`, `pipenv list`, `pip list`). Fastman intentionally does not
wrap that — pick the one you already know.
:::

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

### `config:appkey`

Generates a new `SECRET_KEY` and updates `.env`.

```bash
fastman config:appkey [--show]
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
