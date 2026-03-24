---
sidebar_position: 2
---

# What's New

Stay up to date with the latest Fastman releases and features.

---

## v0.3.3 (Cheetah) — March 2026

**Persistent env switching, configurable docs, public directory, and Keycloak Swagger auth**

### Persistent Environment Switching

Use `fastman env --source=` to lock an environment. All subsequent `fastman serve` calls will use it automatically — no `--env` flag needed.

```bash
# Lock to development
fastman env --source=development

# Now serve uses .env.development automatically
fastman serve

# Check what's active
fastman env

# Clear the lock, return to auto-detect
fastman env --reset
```

The selection is stored in `.fastman-env` (add to `.gitignore`). You can always override temporarily with `fastman serve --env=staging`.

### Configurable Documentation URLs

Swagger and Redoc paths are now configurable via settings instead of hardcoded:

```env
# .env
DOCS_URL=/docs
REDOC_URL=/redoc
```

Set to empty to disable: `DOCS_URL=` disables Swagger UI. In production, docs are automatically disabled when `DEBUG=false`.

### Public Directory

All scaffold patterns now include a `public/` directory, mounted at `/public` for serving static files:

```
my-api/
├── app/
├── public/          # Static files (HTML, images, CSS, JS)
│   └── index.html
├── certs/
└── .env
```

Configure the directory name in `.env`:

```env
PUBLIC_DIR=public
```

### Keycloak Swagger Authorize Button

The generated Keycloak middleware now includes `add_swagger_auth=True`, which adds an **Authorize** button to the Swagger UI automatically. No manual OpenAPI schema customization needed.

### Dynamic Route Exclusion

Keycloak middleware now reads `settings.DOCS_URL` and `settings.REDOC_URL` to dynamically build its `exclude_patterns`, along with `/public/*`, `/health`, `/openapi.json`, and `/favicon.ico`.

### Certificate Path Fixes

- `KEYCLOAK_VERIFY_SSL=/certs/cert.pem` now works — leading `/` or `\` is stripped and resolved relative to the project root
- `fastman install:certificate` now shows the resolved certificate directory and target CA bundle paths
- `fastman env` displays certificate paths and certifi CA bundle location

### Simplified SSL Resolution

`_resolve_verify()` now only accepts three values for `KEYCLOAK_VERIFY_SSL`:

| Value | Behavior |
|---|---|
| `certifi` | Checks `certs/` dir first, then certifi CA bundle |
| `false` | Disables SSL verification |
| `certs/my-cert.pem` | Uses that specific certificate file |

---

## v0.3.2 (Cheetah) — March 2026

**Environment-aware serve, certifi auto-install, and Keycloak SSL resilience**

### Environment-Aware Serve

You can now choose which `.env` file to load when starting the development server:

```bash
fastman serve --env=development
fastman serve --env=staging
fastman serve --env=production
```

When `--env` is omitted, Fastman auto-detects `.env.production` if it exists, otherwise `.env`.

### certifi Auto-Install

`fastman install:certificate` now installs `certifi` in the project's venv automatically if it's not already present. No more manual `pip install certifi`.

### Keycloak SSL Resilience

The generated `keycloak.py` now validates all certificate paths before passing them to `verify=`. If a path is missing, it falls back gracefully to system defaults with a clear log message instead of crashing with `FileNotFoundError`.

---

## v0.3.1 (Cheetah) — March 2026

**Keycloak certificate support and documentation refresh**

### Certificate Management for Keycloak and Private Services

Fastman can now trust project-local certificates for Keycloak and other third-party services that use private CAs.

```bash
fastman install:auth --type=keycloak --append-certificate

# or run certificate setup independently
fastman install:certificate
```

Add your `.pem` or `.crt` files to the project's `certs/` directory and Fastman appends them to the Python `certifi` CA bundle.

### Documentation Refresh

- Updated the command reference to include `install:certificate` and `--append-certificate`
- Renamed the relevant command grouping to third-party integrations
- Refreshed README, intro, installation, and auth concept docs for `v0.3.1 (Cheetah)`

---

## v0.3.0 — March 2026

**Passkey authentication, full OAuth scaffolding, and IPython out of the box**

### Passkey (WebAuthn) Authentication

No passwords, no MFA. Users authenticate with their fingerprint, Face ID, hardware security key, or device PIN.

```bash
fastman install:auth --type=passkey
```

Generates a complete authentication module with registration and login flows using the [WebAuthn standard](https://webauthn.io/). After authentication, users receive a JWT session token — same as other auth types.

**Endpoints created:**
- `POST /auth/passkey/register/options` — Get registration challenge
- `POST /auth/passkey/register/verify` — Store new passkey
- `POST /auth/passkey/authenticate/options` — Get login challenge
- `POST /auth/passkey/authenticate/verify` — Verify & get session token
- `GET /auth/passkey/me` — Current user info
- `GET /auth/passkey/credentials` — List registered passkeys
- `DELETE /auth/passkey/credentials/{id}` — Remove a passkey

### Full OAuth Scaffolding

OAuth is no longer a stub. It now generates a complete feature module with provider-specific configuration:

```bash
fastman install:auth --type=oauth --provider=google
fastman install:auth --type=oauth --provider=github
fastman install:auth --type=oauth --provider=discord
```

Each provider comes pre-configured with the correct authorize URL, token URL, userinfo endpoint, and scopes. The generated code includes user creation/update on callback, session management, and logout.

### IPython Included by Default

`ipython` is now a required dependency. `fastman tinker` launches an IPython shell immediately — no extra install step needed.

### Other Changes

- Fixed cross-browser CSS issues in docs site (Safari backdrop-filter, Firefox mask)
- Fixed `install:auth` syntax in all documentation (positional → `--type=` option)
- Updated authentication docs with comparison table and passkey guide

---

## v0.2.6 — March 2026

**Virtualenv compatibility, Oracle driver update, and progress bar**

This release fixes the most common issues new developers hit when starting their first project.

### If you're upgrading

```bash
# With uv
uv tool upgrade fastman

# With pip
pip install --upgrade fastman
```

:::tip Already have an existing project?
If `fastman serve` fails with `Extra inputs are not permitted`, add `extra = "ignore"` to your `Settings.Config` class in `app/core/config.py`. New projects include this automatically.
:::

---

### Server & tooling now work inside virtual environments

The biggest change: all external tool calls (`uvicorn`, `alembic`, `black`, `isort`, `autoflake`, `pytest`, `mypy`) now use `python -m <tool>` instead of calling the bare command. This means commands work correctly inside virtualenvs even when the tool's binary isn't on your PATH.

**Before (v0.2.0):**
```bash
$ fastman serve
# Internally ran: uvicorn app.main:app ...
# ❌ "uvicorn: command not found" inside some venvs

$ fastman database:migrate
# Internally ran: alembic upgrade head
# ❌ "alembic: command not found"
```

**After (v0.2.6):**
```bash
$ fastman serve
# Internally runs: python -m uvicorn app.main:app ...
# ✅ Always works

$ fastman database:migrate
# Internally runs: python -m alembic upgrade head
# ✅ Always works
```

**Affected commands:** `serve`, `make:migration`, `database:migrate`, `migrate:rollback`, `migrate:reset`, `migrate:status`, `optimize`, `build`

---

### Oracle driver updated

`cx_oracle` is deprecated. New Oracle projects now use `oracledb`:

```env
# Before
DATABASE_URL=oracle+cx_oracle://user:pass@localhost:1521/XE

# After
DATABASE_URL=oracle+oracledb://user:pass@localhost:1521/XE
```

The pip dependency also changed from `cx_Oracle` to `oracledb`.

---

### Extra `.env` variables no longer crash the server

When you choose Oracle, PostgreSQL, or MySQL, the generated `.env` includes convenience variables (`ORACLE_USER`, `POSTGRES_PASSWORD`, etc.). Previously these caused a Pydantic `ValidationError` because the `Settings` class didn't declare them:

```
ORACLE_USER
  Extra inputs are not permitted
```

**Fix:** The generated config now uses environment-aware loading with `extra = "ignore"`:

```python
def _get_env_file() -> str:
    env = os.getenv("ENVIRONMENT", "development")
    env_file = f".env.{env}"
    if Path(env_file).exists():
        return env_file
    return ".env"

class Config:
    env_file = _get_env_file()
    case_sensitive = True
    extra = "ignore"
```

---

### Multi-environment support

Projects now generate four environment files:

- `.env` — Fallback defaults
- `.env.development` — Local dev settings (DEBUG=true, localhost)
- `.env.staging` — Staging settings (staging DB host)
- `.env.production` — Production settings (DEBUG=false, restricted hosts)

The `ENVIRONMENT` variable controls which file is loaded. All `fastman` commands that modify env vars (auth, key:generate, etc.) update **all** env files automatically.

### Per-provider database settings

Database configuration now uses individual fields instead of a single `DATABASE_URL`:

```python
DB_HOST: str = "localhost"
DB_PORT: int = 5432
DB_USER: str = "postgres"
DB_PASSWORD: str = ""
DB_NAME: str = "myapp"

@computed_field
@property
def database_url(self) -> str:
    return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
```

You can still set `DATABASE_URL` directly to override the computed value.

---

### Progress bar for `fastman new`

Project creation now shows a single real-time progress bar instead of printing individual file/directory creation messages:

```
⠋ Setting up project directories...  ━━━━━━━━━━━╺━━━━━━━━━  30%
```

---

### New and updated flags

Several flags that were already implemented in the CLI are now fully documented, exposed in `--help` output, and included in shell completions.

#### `fastman new` — `--graphql` and `--minimal` flags

```bash
# Scaffold a project that includes GraphQL support out of the box
fastman new gql-api --graphql

# Skip optional dev dependencies (faker, pytest, httpx)
fastman new tiny-api --minimal
```

- `--graphql` generates `app/core/graphql.py` and adds `strawberry-graphql[fastapi]` to dependencies.
- `--minimal` omits `faker`, `pytest`, and `httpx` from dependencies.

#### `fastman serve` — explicit `--reload` flag

`--reload` is now an explicit flag alongside the existing `--no-reload`. The default behaviour (reload enabled) is unchanged.

```bash
fastman serve --reload      # explicit; same as default
fastman serve --no-reload   # disable reload for production-like runs
```

#### `fastman activate` — `--create-script` flag now visible

`--create-script` was already implemented but not shown in `--help`. It now appears in the usage line:

```bash
fastman activate --create-script
```

Creates a small helper script (`activate.sh` / `activate.bat`) in the project directory alongside printing the activation command.

#### `fastman make:api` — correct flag is `--style`

The flag to choose between REST and GraphQL output has always been `--style` (not `--type`). The docs now reflect this correctly:

```bash
fastman make:api orders --style=rest      # default
fastman make:api orders --style=graphql
```

#### `fastman install:auth` — `--provider` option

An optional `--provider` value can be passed for OAuth flows:

```bash
fastman install:auth --type=oauth --provider=google
```

#### `fastman docs` and `fastman completion` — flags now in help

```bash
fastman docs --open            # open the docs site in your browser
fastman completion bash --install  # install completion, not just print it
```

---

### Other fixes

| Area | What changed |
| --- | --- |
| **pip on Windows** | Venv pip path now resolves correctly (`.venv\Scripts\pip.exe`) |
| **Package manager detection** | Falls back to `pip` when `uv` isn't installed; detects `requirements.txt`-only projects |
| **`fastman new` on existing dir** | Now exits with code 1 instead of silently returning |
| **Banner rendering** | Gracefully handles missing/corrupt Pyfiglet fonts |
| **Docker CMD** | Generated Dockerfile uses `python -m` for alembic and uvicorn |

---

## v0.2.0 — February 2026

**Professional console UI, shell completions, and virtual environment management**

The first major update after the initial release, focused on developer experience.

### Professional Console UI

All CLI output is now styled with [Rich](https://github.com/Textualize/rich) (when installed), with Laravel-inspired aesthetics:

```bash
> Project 'my-api' created successfully!

>> Next steps:
  cd my-api - Navigate to project directory
  fastman serve - Start the development server
  fastman list - View all available commands
```

New methods available for custom commands: `Output.section()`, `Output.task()`, `Output.listing()`, `Output.highlight()`, `Output.comment()`, `Output.ask()`, `Output.choice()`, `Output.confirm()`, `Output.progress()`, `Output.spinner()`

### Shell completions

Tab completion for all commands and options. Install with one command:

```bash
fastman completion bash --install   # Bash
fastman completion zsh --install    # Zsh
fastman completion fish --install   # Fish
fastman completion powershell --install  # PowerShell
```

### Virtual environment activation

Don't remember the activation command for your OS? Just run:

```bash
fastman activate
# Shows: source .venv/bin/activate    (Linux/Mac)
# Shows: .\.venv\Scripts\activate     (Windows)
```

### 29 integration tests

Real filesystem tests (not mocks) covering project creation, feature scaffolding, utilities, template rendering, and CLI behaviour.

### Bug fixes

- `pyproject.toml` syntax error fixed
- All subprocess calls have timeouts (30–300 s)
- CLI option parsing handles both `--name=value` and `--name value`
- File operations handle `PermissionError` and `IsADirectoryError` specifically
- Path traversal protection
- Secure key generation via `secrets.token_urlsafe()`

---

## v0.1.0 — January 2026

**Initial release** — 30+ commands for FastAPI development.

### Project & scaffolding

```bash
fastman new my-api --pattern=feature --database=postgresql
fastman make:feature users --crud
fastman make:model post
fastman make:service payment
fastman install:auth --type=jwt
```

### Database & migrations

```bash
fastman make:migration "create users table"
fastman database:migrate
fastman migrate:rollback --steps=2
fastman database:seed
```

### Dev tools

```bash
fastman serve              # Start dev server with hot reload
fastman tinker             # Interactive shell with DB session
fastman route:list         # Show all API routes
fastman generate:key       # Generate SECRET_KEY
fastman optimize           # Run black + isort + autoflake
```

### Highlights

- **Rich & Pyfiglet included** — Styled output and banners out of the box
- **Smart package detection** — Auto-detects uv, poetry, pipenv, or pip
- **5 databases** — SQLite, PostgreSQL, MySQL, Oracle, Firebase
- **3 architecture patterns** — Feature (vertical slices), API, Layer (MVC-style)
- **Auth scaffolding** — JWT, OAuth, Keycloak
