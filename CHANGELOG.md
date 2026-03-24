# Changelog

All notable changes to Fastman will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

- **Progress bar for project creation**: `fastman new` now shows a real-time progress bar (using Rich) instead of individual task lines, giving clearer feedback during scaffolding and dependency installation
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
- **Existing project directory**: `fastman new` now exits with code 1 (instead of silently returning) when the target directory already exists
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

- **Project**: `new`, `serve`, `init`, `build`, `activate`
- **Scaffolding**: `make:feature`, `make:model`, `make:service`, `make:controller`, `make:middleware`, `make:schema`, `make:repository`, `make:command`, `make:exception`, `make:dependency`, `make:websocket`, `make:test`, `make:seeder`, `make:factory`, `make:api`
- **Database**: `make:migration`, `database:migrate`, `migrate:rollback`, `migrate:reset`, `migrate:status`, `database:seed`
- **Dev tools**: `serve`, `tinker`, `route:list`, `generate:key`, `config:cache`, `config:clear`, `cache:clear`, `optimize`, `inspect`
- **Auth**: `install:auth jwt|oauth|keycloak`
- **Utilities**: `list`, `version`, `docs`, `package:import`, `package:remove`
- Auto-detection of uv / poetry / pipenv / pip
- SQLite, PostgreSQL, MySQL, Oracle, Firebase support
- Feature / API / Layer architecture patterns
- Zero-dependency core (Rich and Pyfiglet optional)

---

[Unreleased]: https://github.com/acathon/fastman-cli/compare/v0.3.1...HEAD
[0.3.1]: https://github.com/acathon/fastman-cli/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/acathon/fastman-cli/compare/v0.2.6...v0.3.0
[0.2.6]: https://github.com/acathon/fastman-cli/compare/v0.2.0...v0.2.6
[0.2.0]: https://github.com/acathon/fastman-cli/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/acathon/fastman-cli/releases/tag/v0.1.0
