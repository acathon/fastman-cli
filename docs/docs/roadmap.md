---
sidebar_position: 3
---

# Roadmap

Planning and priorities for upcoming Fastman releases.

---

## v0.5.x "Eagle" — Next Major Release

The Dolphin (v0.4.0) release delivered the high-priority codegen safety + DX
items. v0.5.x focuses on **template maintainability**, **safer auth/mail
injection**, and **mid-project lifecycle** support.

---

### High Priority

#### 1. Extract auth + mail templates from inline strings

`auth.py` embeds full service/router/model code as ~1000+ line string literals.
`mail.py` shipped in v0.4.0 with the same pattern (~450 lines of inline templates).
Both are hard to maintain, review, or lint.

Now that the template engine is Jinja2 (v0.4.0), the path is clearer:

- Move templates to separate `.py.j2` files under `src/fastman/_templates/`
- Use `jinja2.PackageLoader("fastman", "_templates")` for include support
- Enable syntax highlighting + linting on the template content
- Allow templates to share fragments via `{% include %}` / `{% extends %}`

#### 2. Resilient AST-based config injection

`install:auth` and `install:mail` use string `.replace()` on `app/main.py` and
`app/core/config.py`. If the user has customized those files, the replacements
silently fail or corrupt the file.

- Use AST-aware insertion or marker comments for injection points
- Validate file structure before modifying
- Refuse to inject if shape is unrecognized

#### 3. `fastman update` command — mid-project lifecycle

Once `fastman create` runs, the tool never touches the project again. There's
no upgrade story for adopting new template features or pulling in security fixes.

- Diff project files against the latest template
- Offer per-file upgrade with diff preview
- Track template version in `.fastmanrc`

---

### Medium Priority

#### 4. Wire remaining `.fastmanrc` keys

Keys already working: `env`, `pattern`, `package_manager`, `database`. Keys to wire up:

| Key | Purpose |
|-----|---------|
| `host` | Default serve host |
| `port` | Default serve port |
| `python` | Python executable path |
| `auth` | Auth provider |
| `mail` | Mail provider |

#### 5. Robust database seeder discovery

`DatabaseSeedCommand` uses `importlib.import_module()` on `*_seeder.py` files
without validating they have a `Seeder` class with a `run()` method.

- Validate seeder class signature before execution
- Add error recovery so one broken seeder doesn't crash the entire seed operation
- Clean up `sys.path` on exception

#### 6. Configurable subprocess timeouts

Hardcoded 300s for package install and 60s for route discovery may be insufficient
in CI/CD or slow network environments.

- Read timeouts from `.fastmanrc` or environment variables
- Provide sensible defaults with override capability

#### 7. `make:feature --include` flag

Additive convenience: let one command scaffold a feature plus its tests, seeder,
factory, websocket, or migration in a single invocation.

```bash
fastman make:feature orders --crud --include=tests,seeder,factory
```

---

### Low Priority / Polish

#### 8. Generated code syntax validation

Run `ast.parse()` on generated Python files before writing to catch template
errors early rather than at runtime.

#### 9. Ruff integration in generated projects

Wire `ruff` into generated projects' `pyproject.toml` templates with a sensible
default configuration.

#### 10. Rich-first terminal improvements

Shared panel/key-value helpers already added in Cheetah. Continue upgrading
remaining commands to branded Rich layouts.

---

### Out of Scope (Future)

- Multi-tenant authentication support
- Alternative migration tools (Flyway, Liquibase)
- GraphQL-first project pattern
- Plugin system for third-party command packages

---

## Completed in v0.4.0 "Dolphin"

- ✅ Python keyword + builtin guard on `NameValidator`
- ✅ Smart pluralization (sibilants, consonant+y, Latin/Greek, irregulars, mass nouns)
- ✅ Auto-generated shell completions from `COMMAND_REGISTRY`
- ✅ Version pins in generated `requirements.txt`
- ✅ `.fastmanrc` in generated `.gitignore`
- ✅ `MANIFEST.in` cleanup
- ✅ Pattern-aware `make:*` commands via `.fastmanrc`
- ✅ Mail scaffolding (`install:mail` + `make:mail`, fastapi-mail, 4 providers)
- ✅ **Template engine swapped to Jinja2** (order-independent, StrictUndefined catches missing keys, fixed a latent nested-substitution bug for postgres/mysql)
- ✅ Venv-aware `PackageManager` (project's `.venv` pip is used even when not activated)
- ✅ Alembic env.py walks feature/api models so autogenerate sees them
- ✅ `database:migrate` & friends refuse to run when `alembic.ini` is missing
- ✅ SQLAlchemy 2.0 + Pydantic v2 codegen
- ✅ 7 low-leverage commands removed (package:*, config:cache/clear, inspect, migrate:reset)

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
