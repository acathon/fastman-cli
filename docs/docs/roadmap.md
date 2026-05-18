---
sidebar_position: 3
---

# Roadmap

Planning and priorities for upcoming Fastman releases.

---

## v0.5.x "Eagle" — Next Major Release

The Dolphin (v0.4.x) line cleared the high-priority codegen-safety,
template-maintainability, and mid-project-lifecycle items. v0.5.x will
focus on **polish wave** wins, **multi-tenant authentication** support,
and **richer model introspection**.

---

### High Priority

#### 1. Interactive `fastman create` wizard

Multi-step prompt flow walks new users through `pattern -> database ->
package_manager -> graphql` instead of requiring all flags up front.

- Build on the existing `prompt_argument` + `Output.choice` helpers
- Honor `--no-interaction` for CI parity with the rest of `make:*`
- Default to the same shape as the current flagless `fastman create`

#### 2. Multi-tenant authentication support

`install:auth` currently assumes a single-tenant model. Add a tenancy
mode where users belong to organizations / workspaces, with
organization-scoped permissions.

- New `User.organization_id` foreign key in the JWT/OAuth/Passkey models
- `get_current_organization` dependency next to `get_current_user`
- Optional `--multi-tenant` flag on `install:auth`

---

### Medium Priority

#### 3. Wire remaining `.fastmanrc` keys

Keys already working: `env`, `pattern`, `package_manager`, `database`. Keys to wire up:

| Key | Purpose |
|-----|---------|
| `host` | Default serve host |
| `port` | Default serve port |
| `python` | Python executable path |
| `auth` | Auth provider |
| `mail` | Mail provider |

#### 4. Robust database seeder discovery

`DatabaseSeedCommand` uses `importlib.import_module()` on `*_seeder.py` files
without validating they have a `Seeder` class with a `run()` method.

- Validate seeder class signature before execution
- Add error recovery so one broken seeder doesn't crash the entire seed operation
- Clean up `sys.path` on exception

#### 5. Configurable subprocess timeouts

Hardcoded 300s for package install and 60s for route discovery may be insufficient
in CI/CD or slow network environments.

- Read timeouts from `.fastmanrc` or environment variables
- Provide sensible defaults with override capability

#### 6. `make:feature --include` flag

Additive convenience: let one command scaffold a feature plus its tests, seeder,
factory, websocket, or migration in a single invocation.

```bash
fastman make:feature orders --crud --include=tests,seeder,factory
```

---

### Low Priority / Polish

#### 7. Generated code syntax validation

Run `ast.parse()` on generated Python files before writing to catch template
errors early rather than at runtime.

#### 8. Ruff integration in generated projects

Wire `ruff` into generated projects' `pyproject.toml` templates with a sensible
default configuration.

#### 9. Rich-first terminal improvements

Shared panel/key-value helpers already added in Cheetah. Continue upgrading
remaining commands to branded Rich layouts.

---

### Out of Scope (Future)

- Alternative migration tools (Flyway, Liquibase)
- GraphQL-first project pattern
- Plugin system for third-party command packages

---

## Completed in v0.4.2 "Dolphin"

- ✅ **`route:list --json`** — machine-readable JSON for editors / CI
- ✅ **`db:fresh`** — one-shot wipe + migrate + (optional) seed, with production guard
- ✅ **`model:show <name>`** — SQLAlchemy model introspection (columns / relations / indexes)
- ✅ 13 new fast unit tests

## Completed in v0.4.1 "Dolphin"

- ✅ **AST-aware code injection** for `install:auth --type=keycloak` and `install:mail` — survives anchor renames, idempotent on re-run, parse-validated before write
- ✅ **`fastman update` command** — diff drifted fastman-owned files against current templates, interactive review or `--check` for CI, closes the mid-project lifecycle gap
- ✅ Marker-bracket convention (`# fastman:<tag>:start` / `:end`) so re-running installs replaces blocks instead of duplicating
- ✅ 26 new fast unit tests (13 injection + 13 update)

## Completed in v0.4.0 "Dolphin"

- ✅ **Mail scaffolding** (`install:mail` + `make:mail`, fastapi-mail, 4 providers)
- ✅ **Template engine swapped to Jinja2** (order-independent, StrictUndefined catches missing keys, fixed a latent nested-substitution bug for postgres/mysql)
- ✅ **Auth + mail templates extracted to `.j2` files** — `auth.py` shrunk from 1,403 → 358 lines, `mail.py` from 530 → 297 lines
- ✅ **SQLAlchemy 2.0 + Pydantic v2 codegen** in all generated projects
- ✅ Python keyword + builtin guard on `NameValidator`
- ✅ Smart pluralization (sibilants, consonant+y, Latin/Greek, irregulars, mass nouns)
- ✅ Auto-generated shell completions from `COMMAND_REGISTRY`
- ✅ Version pins in generated `requirements.txt`
- ✅ `.fastmanrc` in generated `.gitignore`
- ✅ `MANIFEST.in` cleanup
- ✅ Pattern-aware `make:*` commands via `.fastmanrc`
- ✅ Venv-aware `PackageManager` (project's `.venv` pip is used even when not activated)
- ✅ Alembic env.py walks feature/api models so autogenerate sees them
- ✅ `database:migrate` & friends refuse to run when `alembic.ini` is missing
- ✅ 6 low-leverage commands removed (`package:list`, `config:cache`/`:clear`, `inspect`, `migrate:reset`, `package:import` renamed to `package:install`)
- ✅ `fastman about` — one-screen project diagnostic
- ✅ Interactive prompts on `make:*` + global `--no-interaction` / `-n` flag
- ✅ 100% help-text coverage across all 42 commands

## Completed in v0.3.x "Cheetah"

- ✅ Rich console output with branded theme
- ✅ 5 database drivers (SQLite, PostgreSQL, MySQL, Oracle, Firebase)
- ✅ 4 auth types (JWT, OAuth, Keycloak, Passkey)
- ✅ 3 architecture patterns (Feature, API, Layer)
- ✅ Non-destructive SSL certificate handling
- ✅ Graceful Keycloak startup with public-client fallback
- ✅ Shell completions (Bash, Zsh, Fish, PowerShell)
- ✅ Environment management with `.fastmanrc` (originally `.fastman`)
- ✅ `install:cert` merged CA bundle command
- ✅ Ruff replaced black/isort/autoflake
- ✅ 44 tests (unit + integration)
