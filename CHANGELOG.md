# Changelog

All notable changes to Fastman will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.1] "Dolphin" - 2026-05-18

Additive patch on top of 0.4.0. Two new pieces, both backward-compatible:

### ✨ Added

- **AST-aware code injection (`src/fastman/injection.py`).**
  `install:auth --type=keycloak` and `install:mail` previously patched
  `app/main.py` and `app/core/config.py` via brittle `str.replace()` on
  anchor strings. If the user renamed an anchor or reordered imports,
  the install silently no-oped — but the command still reported success,
  leaving the user with an app that didn't actually wire up the new
  feature. The new module exposes:
  - `inject_block()` — wraps the inserted code in
    `# fastman:<tag>:start` / `# fastman:<tag>:end` markers so re-runs
    replace instead of duplicating, with a fallback string anchor when
    no markers are present yet.
  - `inject_into_class_body()` — parses the file with `ast`, locates
    the target class structurally, and appends the marker-bracketed
    block to the end of its body. The user's anchor-comment renames
    are irrelevant because we navigate the class definition, not the
    literal text around it.
  Every injection runs `ast.parse()` on the post-write result and
  aborts if the file wouldn't parse, leaving the user's file
  untouched. Returns explicit `INSERTED` / `REPLACED` / `SKIPPED` /
  `FAILED` status — no more silent no-op.

- **`fastman update` command.** Re-scaffolds drifted fastman-owned
  files against the current version's templates. For each file fastman
  originally generated (database.py, config.py, alembic/env.py, mail/,
  ...), renders the current template using the project's recorded
  `.fastmanrc` and compares it to what's on disk. The user picks
  keep/update per file. Modes:
  - `fastman update` — interactive review with `[u]pdate / [k]eep /
    [a]ll remaining / [q]uit`.
  - `fastman update --check` — drift report only, exit 1 if anything
    differs (CI-friendly).
  - `fastman update --all` — apply every drift without prompting.
  - `fastman update --file=<path>` — narrow to one file.
  - `fastman update --mail` / `--auth` — narrow by integration scope.
  Files fastman did not originate (your features, routes, models) are
  never touched. A pre-0.4.0 project without `.fastmanrc` still works
  via filesystem inference. **This closes the mid-project lifecycle
  gap — projects can now adopt new template improvements (SQLAlchemy
  2.0, Pydantic v2 ConfigDict, etc.) without recreating from scratch.**

### 🔧 Fixed

- The naive `str.replace()` in `install:auth --type=keycloak` and
  `install:mail` could silently no-op when users renamed anchor
  comments. Both now go through AST-aware injection (see above) and
  report `INSERTED` / `REPLACED` / `SKIPPED` / `FAILED` explicitly.

### Tests

13 unit tests for injection (markers, idempotence, parse-validation,
hard fail without touching user file). 13 unit tests for update (zero
drift on fresh project, modified-file detection, missing-file
detection, all four database variants, fallback inference). 56 fast
tests pass overall.

## [0.4.0] "Dolphin" - 2026-05-18

This release tightens the command surface, modernizes generated code for
SQLAlchemy 2.0 / Pydantic v2, adds first-class mail scaffolding, and pulls
shell completions out of the static lookup table they used to live in.

### ⚠️ Breaking

- **6 commands removed.** They were either pure wrappers around the underlying
  package manager / FS or dead code that wrote files nothing read:
  `package:import`, `package:list`, `config:cache`, `config:clear`, `inspect`,
  `migrate:reset`. Use `uv pip list` / `pip list`, `fastman cache:clear`,
  `fastman route:list`, or raw `alembic` respectively.
- **Note**: `package:install` and `package:remove` were briefly cut and then
  restored with venv-aware behaviour (see Added below) — they earn their keep
  by routing pip installs into the project's `.venv` even when the user hasn't
  activated it.
- **Three env files, not four.** `fastman create` now scaffolds `.env`,
  `.env.develop`, and `.env.staging` only. `.env.production` is intentionally
  not generated — production secrets should come from a real secrets manager
  (AWS SSM, Vault, k8s secrets) rather than a committed placeholder. The
  default value of `ENVIRONMENT` is now `develop` (was `development`), and
  `fastman serve` auto-detects `.env.develop` then `.env`.
- **Generated `app/core/database.py` now subclasses `DeclarativeBase`** (SQLAlchemy
  2.0) instead of calling `declarative_base()`. Existing models built on the
  old `Base` still work — `DeclarativeBase` is backward-compatible with the
  imperative `Column(...)` style — but new `make:feature` / `make:model`
  output uses typed `Mapped[...]` columns.
- **Generated Pydantic schemas use `model_config = ConfigDict(...)`** instead
  of the nested `class Config:` block. Affects `make:feature`,
  `make:model`, `make:schema`, and `install:auth` output.
- **`Settings` uses `SettingsConfigDict`** instead of `class Config` for the
  Pydantic v2 way of declaring `env_file` / `extra` / `case_sensitive`.
- **Template engine swapped to Jinja2.** The homegrown `str.replace()` engine
  was single-pass-but-order-dependent (a value containing a placeholder
  would only get re-substituted when the dict happened to iterate in the
  right order — actively masking the postgres/mysql `{project_name}` nested-
  reference bug). All template placeholders are now `{{ name }}` instead of
  `{name}`, missing variables raise loudly (`StrictUndefined`), and rendering
  is order-independent. `jinja2>=3.1.0` is now a dependency.

### ✨ Added

- **`package:install` and `package:remove` (venv-aware).** Routes through the
  right backend (uv / poetry / pipenv / pip) and, on the pip backend,
  resolves the project's `.venv` / `venv` / `env` pip binary directly so the
  install lands in the project even when the user hasn't activated the venv.
  Previously fastman used `sys.executable`, which could be the global
  interpreter when the CLI is installed system-wide. The same fix benefits
  every command that installs packages (`install:auth`, `install:mail`,
  `optimize`, `install:cert`).
- **Production explicitly maps to `.env`.** Setting `ENVIRONMENT=production`
  (or `fastman serve --env=production`) now reads the bare `.env` file by
  design — that's the file the deployment platform populates from its
  secrets manager. No more silent fallback semantics.
- **Alembic fixes.** Four bugs in generated `alembic/env.py`:
  - `settings.DATABASE_URL` was `None` for PostgreSQL / MySQL / Oracle
    (those configs expose the URL via the lowercase `database_url`
    computed property). Migrations now read either source, with a clear
    error if neither is set.
  - `from app.models import *` missed models living inside feature folders
    (`app/features/<name>/models.py`). Generated migrations were silently
    empty for the flagship `make:feature --crud` → `make:migration` flow.
    Now walks `app/models/`, `app/features/*/models.py`, and
    `app/api/*/models.py` to populate `Base.metadata`.
  - `parents[2]` pointed one level above the project root; corrected to
    `parents[1]`.
  - `make:migration` / `database:migrate` / `migrate:rollback` /
    `migrate:status` now refuse to run when `alembic.ini` is missing,
    with an actionable message ("This project doesn't use Alembic
    migrations — Firebase projects don't scaffold it.") instead of a
    cryptic alembic stack trace.
- **`install:mail` and `make:mail` commands.** Wires up `fastapi-mail` with
  per-provider env defaults (SMTP, SendGrid, Mailgun, AWS SES), a `Mailable`
  base class supporting both `.send()` and `.send_later(background_tasks)`,
  and template scaffolding. `make:mail` ships an `--markdown` flag that
  renders Markdown templates via `markdown-it-py` at send time.
- **`NameValidator.pluralize()`** with irregulars, sibilant endings, Latin/
  Greek `-is → -es`, and mass nouns. Wired into `make:feature` and
  `make:model` so `__tablename__`, router prefixes, and `list_*` function
  names use real plurals (`address → addresses`, `category → categories`,
  `analysis → analyses`).
- **Python keyword / builtin guard on `NameValidator`.** Project, feature,
  and model names that collide with reserved words (`class`, `True`),
  soft keywords (`type`, `match`), or builtins (`list`, `dict`) are
  rejected with an actionable error before any code is generated.
- **`.fastmanrc` records project shape.** `fastman create` now persists
  `pattern`, `package_manager`, and `database`. The `make:*` commands read
  this to give a pattern-specific error when called in the wrong project
  (e.g. `make:controller` in a feature-pattern project). The env-locking
  feature previously written to `.fastman` now lives in the same file.
- **Per-pattern command guide in the generated README.** Each project's
  README now lists the `make:*` commands that fit the chosen pattern and
  flags the ones that don't.
- **Dynamic shell completion.** `shell_completion.py` now reads commands,
  options, and flags directly from `COMMAND_REGISTRY` + `parse_signature`.
  Adding a new `@register`'d Command lights up bash / zsh / fish /
  powershell automatically — no second list to maintain.
- **Version-pinned requirements.txt fallback.** Lower bounds emitted for
  every generated dependency (`fastapi>=0.110`, `sqlalchemy>=2.0`,
  `pydantic-settings>=2.1`, ...) so fresh installs land on known-good
  versions.

### 🔧 Fixed

- **MANIFEST.in contradictory rules.** Removed the orphaned
  `recursive-include docs/assets` line that the next-line exclude was
  wiping out.
- **`.fastmanrc` in generated `.gitignore`** so the per-project config isn't
  committed accidentally.

### 📚 Documentation

- Updated `fastman create --help` with explicit "when to pick this pattern"
  guidance for each of API / Feature / Layer.
- Updated `docs/whats-new.md` and version references across the docs site.

## [0.3.6] - 2026-03-26

### ✨ Added

- **`install:cert` command**: Fastman's certificate utility now builds a merged CA bundle from `certifi` plus project certificates and writes `CERTS_PATH`, `REQUESTS_CA_BUNDLE`, and `SSL_CERT_FILE` into env files when needed
- **Graceful Keycloak startup**: generated `app/core/keycloak.py` now lets the API start even when Keycloak is unreachable during boot. Fastman logs the failure, disables Keycloak for that process, and keeps non-Keycloak routes available
- **Public-client fallback**: when Keycloak returns `unauthorized_client` while requesting an admin token, Fastman now retries without admin features so basic route protection and `/me` can still be used
- **Non-destructive SSL certificate loading**: generated Keycloak projects build a merged CA bundle from `certifi` plus project certificates and set `REQUESTS_CA_BUNDLE` / `SSL_CERT_FILE` instead of editing `certifi` in place

### 📚 Documentation

- Rewrote the Keycloak auth guide to distinguish minimal auth setup from admin-enabled setup
- Documented that `KEYCLOAK_ADMIN_SECRET` is optional unless your code uses admin operations on `idp`
- Renamed certificate setup docs to `install:cert` and documented `install:certificate` as a deprecated alias
- Updated the docs site, installation page, landing page, and release banner to `v0.3.6`

## [0.3.5] - 2026-03-25

### ⚠️ Breaking

- **Keycloak: switched from `fastapi-keycloak-middleware` to `fastapi-keycloak`**: The generated `app/core/keycloak.py` now uses a `FastAPIKeycloak` instance with dependency-based route protection instead of global middleware. Routes are no longer protected by default — add `Depends(get_current_user)` to each protected endpoint. New env variables: `KEYCLOAK_ADMIN_SECRET`, `KEYCLOAK_CALLBACK_URI`. Removed: `KEYCLOAK_VERIFY_SSL=certifi` file-path mode.

### ✨ Added

- **Keycloak `/me` endpoint**: `init_keycloak(app)` now registers a `GET /me` route that returns the current `OIDCUser` via `Depends(get_current_user)`
- **Lazy Keycloak initialization**: `FastAPIKeycloak` instance is now created inside `init_keycloak(app)` instead of at module level — no network calls at import time, preventing SSL crashes when Keycloak is unreachable during import
- **Auto certificate appending**: `init_keycloak()` automatically scans `certs/` (or `CERTS_PATH` env var) for `.pem`/`.crt` files, builds a merged CA bundle, and sets `REQUESTS_CA_BUNDLE` — no separate script or manual step needed, and the original certifi bundle is never modified
- **Graceful Keycloak fallback**: the app no longer crashes if Keycloak is unreachable (connection refused) or configured with a public client (`unauthorized_client`). The server starts with Keycloak disabled and logs a clear warning

## [0.3.4] - 2026-03-25

### ✨ Added

- **Persistent environment switching**: `fastman env --source=development` saves the selection to `.fastman`; subsequent `fastman serve` calls use it automatically without `--env`
- **`fastman env` command**: Shows active environment file, variables (with sensitive values masked), certificate paths, and certifi CA bundle location
- **`--reset` flag**: `fastman env --reset` clears the lock and returns to auto-detect behavior
- **Configurable docs URLs**: `DOCS_URL` and `REDOC_URL` settings in config and `.env` files — change or disable Swagger/Redoc paths
- **Public directory**: New `public/` directory in all scaffold patterns, mounted at `/public` for serving static files (HTML, images, etc.)
- **Keycloak Swagger Authorize button**: Generated `keycloak.py` now uses `add_swagger_auth=True` for built-in OpenAPI auth support
- **Dynamic route exclusion**: Keycloak middleware excludes docs/redoc/public routes dynamically from `settings.DOCS_URL` and `settings.REDOC_URL`

### 🔧 Fixed

- **Certificate path with leading slash**: `KEYCLOAK_VERIFY_SSL=/certs/cert.pem` now resolves correctly (leading `/` or `\` is stripped and treated as relative to project root)
- **SSL verify resolution simplified**: `_resolve_verify()` now only supports `certifi`, `false`, or a file path — removed `true` option to avoid ambiguity
- **`install:certificate` shows real paths**: Displays the resolved `certs/` directory path and the target certifi CA bundle path for easier debugging

## [0.3.2] - 2026-03-24

### ✨ Added

- **Environment-aware serve**: `fastman serve --env=development` loads `.env.development` via uvicorn's `--env-file`. Auto-detects `.env.production` or `.env` when no flag is given
- **certifi auto-install**: `fastman install:certificate` now installs `certifi` in the project venv automatically if missing
- **Keycloak SSL resilience**: Generated `keycloak.py` validates certificate paths before passing to `verify=`, with graceful fallbacks and logging

### 🔧 Fixed

- **FileNotFoundError on Keycloak SSL**: `_resolve_verify()` now checks `Path.is_file()` before using any certificate path, preventing crashes when certifi bundle or custom cert is missing

## [0.3.1] - 2026-03-24

### ✨ Added

- **Project certificate management**: Added `fastman install:certificate` to append `.pem` and `.crt` files from the project `certs/` directory into the local `certifi` CA bundle
- **Keycloak certificate flow**: `fastman install:auth --type=keycloak --append-certificate` now appends project certificates immediately after Keycloak setup

### 🎨 Changed

- **Command grouping**: Auth and certificate installation commands are now documented under third-party integrations instead of authentication alone

### 📚 Documentation

- Updated README, intro page, installation guide, utility command reference, and authentication concepts for the new certificate workflow
- Updated release docs and version examples to `v0.3.1`

## [0.3.0] - 2026-03-10

### ✨ Added

- **Passkey (WebAuthn) authentication**: `fastman install:auth --type=passkey` scaffolds passwordless auth using biometrics, hardware keys, or device PINs — no passwords or MFA needed
- **Full OAuth scaffolding**: `fastman install:auth --type=oauth --provider=google` now generates complete OAuth flow (config, models, schemas, service, router) instead of only installing packages. Supports Google, GitHub, and Discord out of the box
- **IPython is now a required dependency**: `fastman tinker` works immediately after install without needing `pip install ipython` separately

### 🔧 Fixed

- **OAuth was a stub**: Previously only installed `authlib` and `httpx` with no generated code. Now scaffolds a full OAuth feature module with login, callback, user creation, and logout endpoints
- **Cross-browser CSS compatibility**: Added `-webkit-backdrop-filter` prefixes for Safari, `mask` fallback for Firefox, fixed `min-height: auto` for Firefox in docs site
- **`install:auth jwt` syntax in docs**: Corrected to `install:auth --type=jwt` across all documentation
- **whats-new.md**: Updated "Zero-dependency core" highlight (rich/pyfiglet are now required deps)

### 📚 Documentation

- Rewrote authentication concepts page with full coverage of all four auth types (JWT, OAuth, Keycloak, Passkey)
- Added comparison table of auth types at the top of the auth docs
- Added passkey frontend integration example (JavaScript WebAuthn API)

---

## [0.2.6] - 2026-03-10

### ✨ Added

- **Progress bar for project creation**: `fastman create` now shows a real-time progress bar (using Rich) instead of individual task lines, giving clearer feedback during scaffolding and dependency installation
- **`Output.start_progress()` / `Output.stop_progress()`**: New console methods for managed progress bars

### 🔧 Fixed

- **Server startup crash with Oracle/PostgreSQL/MySQL**: Generated `Settings` class now includes `extra = "ignore"`, preventing `pydantic_core.ValidationError` when `.env` contains database helper variables like `ORACLE_USER`, `POSTGRES_USER`, or `MYSQL_USER`
- **Oracle driver**: Switched from deprecated `cx_oracle` to modern `oracledb` — both the dependency name and the connection string (`oracle+oracledb://`)
- **Alembic commands not found**: All migration commands (`make:migration`, `database:migrate`, `migrate:rollback`, `migrate:reset`, `migrate:status`) now use `python -m alembic` instead of bare `alembic`, fixing "command not found" errors in virtualenvs
- **`fastman serve` failing in venvs**: Server command now uses `python -m uvicorn` instead of bare `uvicorn`
- **`fastman optimize` / `build` tool calls**: `black`, `isort`, `autoflake`, `pytest`, and `mypy` are now invoked via `python -m` to work correctly inside virtual environments
- **Docker CMD**: Generated Dockerfile now uses `python -m alembic` and `python -m uvicorn` so containers work without PATH hacks
- **pip path on Windows**: `_initialize_package_manager` now uses absolute paths to the venv's `pip.exe` on Windows instead of relative Unix-style paths
- **Package manager detection**: `PackageManager.detect()` now correctly falls back to `pip` when no lock files exist and `uv` is not installed; also detects `requirements.txt`-only projects
- **Existing project directory**: `fastman create` now exits with code 1 (instead of silently returning) when the target directory already exists
- **Banner crash**: Pyfiglet font rendering is now wrapped in try/except to handle missing or corrupt fonts gracefully
- **Test reliability**: `test_detect_pip` now properly mocks `shutil.which`; Oracle integration test updated for `oracledb` driver

### 🎨 Changed

- **Cleaner project creation output**: Removed per-file/per-directory creation messages — progress bar replaces individual `file_created()`/`directory_created()` calls
- **Package manager init uses `cwd` param**: All `_create_requirements_txt` fallback calls now correctly pass the project `cwd`

### 📚 Documentation

- Rewrote **What's New** page with real changelog entries for all versions
- Fixed Oracle connection string in database concepts (`oracle+cx_oracle` → `oracle+oracledb`)
- Updated version references across all docs (`v0.3.0` → `v0.2.6`)
- Updated README version badge to `0.2.6`

---

## [0.2.0] - 2026-02-07

### ✨ Added

- **Professional Console UI**: Rich-powered output with `section()`, `task()`, `file_created()`, `directory_created()`, `next_steps()`, `listing()`, `highlight()`, `comment()`, `ask()`, `choice()`, `confirm()`, `progress()`, `spinner()`
- **Shell completions**: `fastman completion {bash|zsh|fish|powershell} --install`
- **Virtual environment management**: `fastman activate` detects OS/shell and shows the right activation command
- **29 integration tests**: Real filesystem tests covering project creation, scaffolding, utilities, templates, and CLI behaviour

### 🔧 Fixed

- `pyproject.toml` syntax error (stray closing bracket)
- Subprocess timeouts added to all calls (30–300 s)
- `option()` method now handles both `--name=value` and `--name value`
- File operations handle `PermissionError`, `IsADirectoryError` specifically
- Better error messages, path validation, and file existence checks

### 🛡️ Security

- Path traversal protection on all user-supplied names
- Stricter identifier validation
- Secret keys generated via `secrets.token_urlsafe()`

---

## [0.1.0] - 2026-01-15

### ✨ Added

**Initial release** with 30+ commands:

- **Project**: `create`, `serve`, `init`, `build`, `activate`
- **Scaffolding**: `make:feature`, `make:model`, `make:service`, `make:controller`, `make:middleware`, `make:schema`, `make:repository`, `make:command`, `make:exception`, `make:dependency`, `make:websocket`, `make:test`, `make:seeder`, `make:factory`, `make:api`
- **Database**: `make:migration`, `database:migrate`, `migrate:rollback`, `migrate:reset`, `migrate:status`, `database:seed`
- **Dev tools**: `serve`, `tinker`, `route:list`, `config:appkey`, `config:cache`, `config:clear`, `cache:clear`, `optimize`, `inspect`
- **Auth**: `install:auth jwt|oauth|keycloak`
- **Utilities**: `list`, `version`, `docs`, `package:import`, `package:remove`
- Auto-detection of uv / poetry / pipenv / pip
- SQLite, PostgreSQL, MySQL, Oracle, Firebase support
- Feature / API / Layer architecture patterns
- Zero-dependency core (Rich and Pyfiglet optional)

---

[Unreleased]: https://github.com/acathon/fastman-cli/compare/v0.4.1...HEAD
[0.4.1]: https://github.com/acathon/fastman-cli/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/acathon/fastman-cli/compare/v0.3.6...v0.4.0
[0.3.6]: https://github.com/acathon/fastman-cli/compare/v0.3.5...v0.3.6
[0.3.5]: https://github.com/acathon/fastman-cli/compare/v0.3.2...v0.3.5
[0.3.2]: https://github.com/acathon/fastman-cli/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/acathon/fastman-cli/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/acathon/fastman-cli/compare/v0.2.6...v0.3.0
[0.2.6]: https://github.com/acathon/fastman-cli/compare/v0.2.0...v0.2.6
[0.2.0]: https://github.com/acathon/fastman-cli/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/acathon/fastman-cli/releases/tag/v0.1.0
