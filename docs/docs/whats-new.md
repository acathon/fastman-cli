---
sidebar_position: 2
---

# What's New

Stay up to date with the latest Fastman releases and features.

---

## v0.4.2 (Dolphin) — May 2026

**Polish wave: JSON route export, one-shot DB reset, model introspection.**

### `route:list --json` for tooling integration

The Rich table is great for humans; tooling needs JSON. `--json` swaps
the table for a flat list of `{methods, path, name}` objects on stdout —
nothing else — so it's safe to pipe directly into editors or CI scripts:

```bash
# All POST routes
fastman route:list --json | jq '.[] | select(.methods | contains(["POST"]))'

# Diff against an expected routes file in CI
diff <(fastman route:list --json) expected-routes.json
```

WebSocket routes (which have no HTTP methods in FastAPI) serialize their
`methods` as `["WS"]`. Filters like `--path=/api/v1` combine cleanly with
`--json`.

### `db:fresh` — one-shot dev reset

The common "blow it away and start fresh" loop is now one command:

```bash
fastman db:fresh                # confirm + downgrade base + upgrade head
fastman db:fresh --seed         # also re-run all seeders
fastman db:fresh --force        # skip the confirmation prompt (CI)
fastman db:fresh --seed --force # full pipeline, unattended
```

What it does under the hood:

1. `alembic downgrade base` — drops every migrated table.
2. `alembic upgrade head` — reapplies every migration.
3. `database:seed` (if `--seed`) — runs all seeders.

**Production safety net.** Even with `--force`, the command refuses to
run when `ENVIRONMENT=production`. If you really need this (you almost
never do), unset the env var or run the alembic commands manually.

### `model:show <name>` — SQLAlchemy introspection

Replaces the `inspect` command dropped in v0.4.0 for the SA-model case
(which was its main use). Walks `app/models/`,
`app/features/*/models.py`, and `app/api/*/models.py`, finds the named
class (tolerant of snake_case / PascalCase), and renders three tables:
columns + types + constraints + defaults; relationships with
direction and collection-vs-singular; indexes.

```bash
fastman model:show User
fastman model:show user_profile    # auto-resolves to UserProfile
```

Example output:

```text
▶ Model: User
  table: users

  Column      | Type           | Constraints       | Default
  id          | INTEGER        | PK NOT NULL INDEX | —
  email       | VARCHAR(255)   | NOT NULL UNIQUE   | —
  name        | VARCHAR(100)   | NOT NULL          | —

  Relations
  Relationship | Target | Direction | Collection
  posts        | Post   | onetomany | yes
```

---

## v0.4.1 (Dolphin) — May 2026

**`fastman update` for mid-project template upgrades, and AST-aware code injection.**

### `fastman update` — re-scaffold drifted files

The biggest mid-project DX gap is closed. Once you ran `fastman create`,
fastman used to never touch your project again — meaning template
improvements (SQLAlchemy 2.0 `DeclarativeBase`, Pydantic v2 `ConfigDict`,
dropped `.env.production`, ...) were stuck until you recreated the
project from scratch.

`fastman update` diffs every file fastman originally generated against
what the current version would generate today and lets you pick
keep/update per file:

```bash
# Interactive — review each drifted file with a unified diff
fastman update

# CI-friendly — exit 1 if anything has drifted
fastman update --check

# Apply every drift without prompting
fastman update --all

# Narrow scope
fastman update --file=app/core/config.py
fastman update --mail          # only files install:mail generated
fastman update --auth          # only files install:auth generated
```

For each file in the catalog (`main.py`, `core/config.py`, `core/database.py`,
`alembic/env.py`, `mail/*`, `auth/<provider>/*`, ...), `update` renders
the current template using your `.fastmanrc` and shows a unified diff:

```text
(1/2)  app/core/database.py  +5 -3 lines
--- app/core/database.py (your version)
+++ app/core/database.py (fastman target)
@@ -1,8 +1,10 @@
-from sqlalchemy.orm import declarative_base, Session, sessionmaker
+from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
 ...
-Base = declarative_base()
+class Base(DeclarativeBase):
+    """Declarative base for all ORM models (SQLAlchemy 2.0 style)."""

  [u]pdate, [k]eep, [a]ll remaining, [q]uit
```

**Files fastman did not originate are never touched.** Your own
features, routes, models, custom middleware, env files — `update` walks
its own catalog, not your project tree. Commit before running, since
there's no rollback inside the command.

Pre-0.4.0 projects without `.fastmanrc` still work via filesystem
inference (the database driver is detected from `app/core/database.py`'s
import strings).

### AST-aware code injection for `install:auth` / `install:mail`

The old `install:auth --type=keycloak` and `install:mail` commands
patched `app/main.py` and `app/core/config.py` using `str.replace()` on
hardcoded anchors like `"    # API"` and
`"from app.core.logging import setup_logging"`. The moment you renamed
a comment or reordered imports, the install silently no-oped while
still reporting success — leaving you with an app that didn't actually
wire up the new feature.

v0.4.1 swaps that out for a hybrid marker + AST strategy:

- **Marker-bracketed blocks.** Inserted code is wrapped in literal
  `# fastman:<tag>:start` / `# fastman:<tag>:end` comments. Re-running
  an install replaces the block between markers in place — idempotent,
  no duplicates.

- **AST class-body insertion.** When fastman injects fields into your
  `Settings` class, it parses the file with `ast` and locates the class
  structurally, not by matching surrounding text. Rename comments,
  reorder fields, add new fields — the next `install:mail` still finds
  `Settings` and appends correctly.

- **Parse-before-write.** Every injection runs `ast.parse()` on the
  result. If injecting would break Python parsing (a template bug, or
  a wildly customized file), the write is aborted and your file is
  left untouched.

- **Explicit status.** Each injection returns `INSERTED` / `REPLACED` /
  `SKIPPED` / `FAILED` with a reason. No more silent failures.

### Tests

26 new fast unit tests (13 for injection, 13 for update). Total 56
fast tests pass.

---

## v0.4.0 (Dolphin) — May 2026

**Lean command surface, modern codegen, mail scaffolding, pattern-aware tooling.**

### Command surface tightened

Six low-leverage commands were removed in favor of the underlying tool:

| Removed | Use this instead |
|---------|------------------|
| `package:import` | `fastman package:install` (new, venv-aware) |
| `package:list` | `uv pip list` / `pip list` |
| `config:cache`, `config:clear` | (dead code — the cache was never read) |
| `inspect` | `fastman route:list` + reading source |
| `migrate:reset` | `alembic downgrade base` (destructive — make it deliberate) |

Net: 46 → 41 commands.

### Smarter package install

`package:install` (renamed from `package:import`) and `package:remove` now
route pip installs through the **project's own `.venv` pip**, even when the
user hasn't activated the venv. Previously fastman used `sys.executable`,
which is the global interpreter when the CLI is installed system-wide — so
`fastman install:auth` could quietly write packages to the wrong env.

```bash
# No need to activate first — package:install finds .venv automatically
fastman package:install requests
fastman package:install "sqlalchemy>=2.0"
```

The same fix benefits `install:auth`, `install:mail`, `install:cert`, and
`optimize` — every command that installs packages.

### Alembic bug fixes

Four bugs in the generated `alembic/env.py` and the migration commands:

- **PostgreSQL/MySQL/Oracle migrations were broken.** Those database configs
  expose `settings.database_url` (lowercase computed property) but
  `alembic/env.py` was reading `settings.DATABASE_URL` (uppercase), which
  was always `None`. The generated env.py now reads either source and
  raises a clear error if neither is set.
- **Feature-pattern models were silently missed by autogenerate.** The
  template used `from app.models import *`, which only picks up models
  registered in `app/models/__init__.py`. Generated feature modules live at
  `app/features/<name>/models.py` — those were never imported, so
  `make:migration` produced empty migration files for the flagship workflow.
  Env.py now walks `app/models/`, `app/features/*/models.py`, and
  `app/api/*/models.py`.
- **`make:migration`, `database:migrate`, `migrate:rollback`,
  `migrate:status`** now refuse to run when `alembic.ini` is missing,
  with an actionable error ("This project doesn't use Alembic — Firebase
  projects don't scaffold it.") instead of a cryptic stack trace.
- `parents[2]` corrected to `parents[1]` in `alembic/env.py`'s `sys.path`
  manipulation.

### Mail scaffolding

New `install:mail` and `make:mail` commands built on `fastapi-mail`:

```bash
fastman install:mail --provider=sendgrid --from=hello@mysite.io
fastman make:mail WelcomeEmail
fastman make:mail OrderShipped --markdown
```

You get:

- `app/core/mail.py` with `FastMail` client, `send_mail()`, `send_mail_background()`
- `app/mail/base.py` with a `Mailable` base class supporting `.send()` and `.send_later(background_tasks)`
- Per-provider env defaults (SMTP, SendGrid, Mailgun, AWS SES)
- `--markdown` flag for templates rendered via `markdown-it-py` at send time

### Modernized generated code

- **SQLAlchemy 2.0**: `app/core/database.py` now uses `class Base(DeclarativeBase)` instead of `declarative_base()`. Generated models use typed `Mapped[]` columns:
  ```python
  class User(Base):
      __tablename__ = "users"
      id: Mapped[int] = mapped_column(primary_key=True)
      email: Mapped[str] = mapped_column(String(255), unique=True)
  ```
- **Pydantic v2**: Generated schemas use `model_config = ConfigDict(from_attributes=True)` instead of the deprecated `class Config` block. `Settings` uses `SettingsConfigDict`.

### Smart pluralization

`__tablename__`, router prefixes, and `list_*` function names now use real English plurals:

| Singular | Old (broken) | New |
|----------|--------------|-----|
| `address` | `addresss` | `addresses` |
| `category` | `categorys` | `categories` |
| `analysis` | `analysiss` | `analyses` |
| `person` | `persons` | `people` |
| `data` | `datas` | `data` |

### Pattern-aware `make:*`

`fastman create` now records `pattern`/`package_manager`/`database` in `.fastmanrc`. When you run a `make:*` command that doesn't fit (e.g. `make:controller` in a feature-pattern project), you get an actionable error instead of "directory not found":

```
✗ 'make:controller' is not the right command for the 'feature' pattern.
  Use one of these instead:
  make:feature, make:model, make:middleware
```

Generated projects also include a per-pattern command guide in the README.

### Keyword + builtin guard

`fastman create class`, `fastman make:feature list`, `fastman make:model True` — all rejected with a clear error *before* any code is generated:

```
✗ Invalid name 'list'. It shadows a Python builtin.
```

### Other polish

- **Dynamic shell completions**: `shell_completion.py` now reads commands and options directly from `COMMAND_REGISTRY` + `parse_signature` — adding a new registered command lights up all four shells (bash / zsh / fish / powershell) with zero edits.
- **Version-pinned requirements**: `requirements.txt` fallback emits lower bounds (`fastapi>=0.110.0`, `sqlalchemy>=2.0.0`, ...).
- **`MANIFEST.in`** cleanup — dropped the contradictory `recursive-include docs/assets *` line that the next-line exclude was wiping out.
- **`.fastmanrc`** added to generated `.gitignore`.

### Breaking changes summary

1. 7 commands removed (see table above).
2. Generated `app/core/database.py` switched to `DeclarativeBase`. Existing models built on `Column(...)` still work — SA 2.0 is backward-compatible.
3. Generated schemas switched to `model_config = ConfigDict(...)`. Old `class Config` blocks in existing projects keep working under Pydantic v2's deprecation shim, but new scaffolds use the modern form.

---

## v0.3.6 (Cheetah) — March 2026

**Safer Keycloak startup, non-destructive SSL certificate handling, and clearer admin credential guidance**

### `install:cert` Command

The certificate utility is now modeled around merged CA bundles instead of patching `certifi`.

- New primary command: `fastman install:cert`
- It builds `certs/ca-bundle-merged.pem` from `certifi` plus your project certificates
- It writes `CERTS_PATH`, `REQUESTS_CA_BUNDLE`, and `SSL_CERT_FILE` into env files when needed
- `install:certificate` remains as a deprecated alias for compatibility

### Graceful Keycloak Startup

Keycloak integration no longer takes your whole app down when the identity provider is unavailable during startup.

- If `KEYCLOAK_URL` is unreachable, Fastman logs the error, disables Keycloak for that boot, and still starts the API
- `/health` and other non-Keycloak routes stay available
- Protected routes continue to work as soon as Keycloak is configured correctly and the app is restarted

### Public Client Compatibility

If Keycloak returns `unauthorized_client` while trying to obtain an admin token, Fastman now treats that as an admin-only limitation instead of a fatal boot error.

- Basic auth flows still work: Swagger authorize, `Depends(get_current_user)`, and `GET /me`
- Admin features are disabled until you provide a confidential admin client with service accounts enabled
- `KEYCLOAK_ADMIN_SECRET` is now documented as optional for projects that do not use admin API methods

### Non-Destructive SSL Certificate Support

Fastman no longer edits the installed `certifi` bundle in place for generated Keycloak projects.

- `init_keycloak()` builds a merged CA bundle from `certifi` plus project certificates
- It sets `REQUESTS_CA_BUNDLE` and `SSL_CERT_FILE` for the running process
- Projects with no `certs/` directory remain unaffected

---

## v0.3.4 (Cheetah) — March 2026

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

The selection is stored in `.fastmanrc` (which is gitignored by default in projects created from Fastman 0.4.0+). You can always override temporarily with `fastman serve --env=staging`.

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

### Keycloak: Switched to `fastapi-keycloak`

Keycloak authentication now uses [`fastapi-keycloak`](https://github.com/fastapi-keycloak/fastapi-keycloak) instead of `fastapi-keycloak-middleware`. Key changes:

- **Dependency injection** — routes are protected via `Depends(get_current_user)` instead of global middleware
- **`GET /me` endpoint** — automatically registered, returns the current OIDC user
- **Swagger Authorize button** — `idp.add_swagger_config(app)` adds OAuth2 auth to Swagger UI
- **User & role management** — the `FastAPIKeycloak` instance (`idp`) exposes methods for creating/deleting users, roles, and groups
- New env variables: `KEYCLOAK_ADMIN_SECRET`, `KEYCLOAK_CALLBACK_URI`

### Lazy Keycloak Initialization & Auto Certificate Appending

The `FastAPIKeycloak` instance is now **lazy-initialized** inside `init_keycloak(app)` instead of at module import time. This solves SSL verification failures that occurred when the IDP tried to contact Keycloak during import.

At startup, `init_keycloak()` automatically:
1. Scans `certs/` (or `CERTS_PATH`) for `.pem`/`.crt` files and builds a merged CA bundle
2. Sets `REQUESTS_CA_BUNDLE` and `SSL_CERT_FILE` for the running process
3. Creates the `FastAPIKeycloak` instance — HTTPS calls now trust your custom certificates
4. Configures Swagger OAuth and registers the `/me` endpoint

No separate certificate script is needed — just drop your cert files in `certs/` and start the server.

### Graceful Keycloak Fallback

The app no longer crashes if Keycloak is unreachable or misconfigured:

- **Connection refused** (Keycloak not running): the app starts with Keycloak disabled, logs a warning, and `/health` still responds
- **Public client** (`unauthorized_client`): the app starts with admin features (user/role management) disabled — basic auth still works
- **Valid Keycloak**: full functionality including admin features and Swagger Authorize button

### Certificate Path Fixes

- `fastman install:certificate` now shows the resolved certificate directory and target CA bundle paths
- `fastman env` displays certificate paths and certifi CA bundle location

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

### Progress bar for `fastman create`

Project creation now shows a single real-time progress bar instead of printing individual file/directory creation messages:

```
⠋ Setting up project directories...  ━━━━━━━━━━━╺━━━━━━━━━  30%
```

---

### New and updated flags

Several flags that were already implemented in the CLI are now fully documented, exposed in `--help` output, and included in shell completions.

#### `fastman create` — `--graphql` and `--minimal` flags

```bash
# Scaffold a project that includes GraphQL support out of the box
fastman create gql-api --graphql

# Skip optional dev dependencies (faker, pytest, httpx)
fastman create tiny-api --minimal
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
| **`fastman create` on existing dir** | Now exits with code 1 instead of silently returning |
| **Banner rendering** | Gracefully handles missing/corrupt Pyfiglet fonts |
| **Docker CMD** | Generated Dockerfile uses `python -m` for alembic and uvicorn |

---

## v0.2.0 — February 2026

**Professional console UI, shell completions, and virtual environment management**

The first major update after the initial release, focused on developer experience.

### Professional Console UI

All CLI output is now styled with [Rich](https://github.com/Textualize/rich) (when installed), with a clean, modern aesthetic:

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
fastman create my-api --pattern=feature --database=postgresql
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
fastman config:appkey      # Generate SECRET_KEY
fastman optimize           # Run black + isort + autoflake
```

### Highlights

- **Rich & Pyfiglet included** — Styled output and banners out of the box
- **Smart package detection** — Auto-detects uv, poetry, pipenv, or pip
- **5 databases** — SQLite, PostgreSQL, MySQL, Oracle, Firebase
- **3 architecture patterns** — Feature (vertical slices), API, Layer (MVC-style)
- **Auth scaffolding** — JWT, OAuth, Keycloak
