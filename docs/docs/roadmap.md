---
sidebar_position: 3
---

# Roadmap

Planning and priorities for upcoming Fastman releases.

---

## v0.4.x "Dolphin" — Next Major Release

Dolphin focuses on **code-generation safety**, **template maintainability**, and **developer experience** improvements built on top of the stable Cheetah (v0.3.x) foundation.

---

### High Priority

#### 1. Python keyword guard on name validation

`NameValidator.validate_identifier()` currently accepts Python reserved words (`class`, `async`, `import`, etc.) as valid names. A project or feature named with a keyword generates broken Python.

- Add `keyword.iskeyword(name)` and `name in dir(builtins)` checks
- Apply to project names, feature names, model names, and all scaffold commands

#### 2. Smart table name pluralization

Generated models use `__tablename__ = "{snake}s"` which produces incorrect plurals like `glasss`, `buss`, `addresss`.

- Implement a lightweight pluralization helper (`s` → `ses`, `y` → `ies`, default → `+s`)
- Cover 90%+ of English nouns without adding a heavy dependency

#### 3. Template engine safety

The current template engine uses raw `str.replace()`. If a variable value happens to contain `{another_placeholder}`, it gets double-substituted.

- Migrate to `string.Template` (`safe_substitute`) or Jinja2
- Add escaping to prevent injection of template variables

#### 4. Extract auth templates from inline strings

`auth.py` embeds full service/router/model code as ~1000+ line string literals. This is extremely hard to maintain, review, or lint.

- Move templates to separate `.py.template` files or into the `Templates` class
- Enable syntax highlighting and linting on template content

#### 5. Auto-generate shell completions from command registry

`shell_completion.py` has a static `COMMANDS` dict instead of pulling from `COMMAND_REGISTRY`. Adding a new command requires updating two places.

- Generate completions dynamically from `COMMAND_REGISTRY` at runtime
- Eliminate the maintenance burden of keeping the list in sync

---

### Medium Priority

#### 6. `make:test` command — Test scaffolding

Scaffold `test_*.py` files with pytest fixtures, client setup, and CRUD test stubs for any feature or model.

- `fastman make:test users` generates `tests/test_users.py`
- Include `TestClient` setup, factory usage, and assertion patterns
- Support `--crud` flag to generate full CRUD test coverage

#### 7. Wire remaining `.fastman` config keys

Keys already working: `env`. Keys to wire up:

| Key | Purpose |
|-----|---------|
| `host` | Default serve host |
| `port` | Default serve port |
| `package_manager` | Preferred package manager override |
| `architecture` | Project scaffold pattern |
| `database` | Database driver |
| `python` | Python executable path |
| `auth` | Auth provider |

#### 8. Resilient config injection for auth

Auth installation uses string replacement on `app/main.py` and `app/core/config.py`. If a user has modified those files, the replacements silently fail or corrupt the file.

- Use AST-aware insertion or marker comments for injection points
- Validate file structure before modifying

#### 9. Robust database seeder discovery

`DatabaseSeedCommand` uses `importlib.import_module()` on `*_seeder.py` files without validating they have a `Seeder` class with a `run()` method.

- Validate seeder class signature before execution
- Add error recovery so one broken seeder doesn't crash the entire seed operation
- Clean up `sys.path` on exception

#### 10. Configurable subprocess timeouts

Hardcoded 300s for package install and 60s for route discovery may be insufficient in CI/CD or slow network environments.

- Read timeouts from `.fastman` config or environment variables
- Provide sensible defaults with override capability

---

### Low Priority / Polish

#### 11. Generated code syntax validation

Run `ast.parse()` on generated Python files before writing to catch template errors early rather than at runtime.

#### 12. Ruff integration in generated projects

Wire `ruff` into generated projects' `pyproject.toml` templates with a sensible default configuration.

#### 13. Rich-first terminal improvements

Shared panel/key-value helpers already added in Cheetah. Continue upgrading remaining commands to branded Rich layouts.

#### 14. `.fastman` in generated `.gitignore`

Generated `.gitignore` doesn't exclude the `.fastman` config file — add it.

#### 15. Version pins in generated `requirements.txt`

Generated projects have no version pins in `requirements.txt`, which can cause compatibility issues on fresh installs.

#### 16. MANIFEST.in cleanup

`MANIFEST.in` includes `docs/assets` then excludes all `docs` — contradictory rules that should be reconciled.

---

### Out of Scope (Future)

- Multi-tenant authentication support
- Alternative migration tools (Flyway, Liquibase)
- GraphQL-first project pattern
- Plugin system for third-party command packages

---

## Completed in v0.3.x "Cheetah"

- ✅ Rich console output with branded theme
- ✅ 5 database drivers (SQLite, PostgreSQL, MySQL, Oracle, Firebase)
- ✅ 4 auth types (JWT, OAuth, Keycloak, Passkey)
- ✅ 3 architecture patterns (Feature, API, Layer)
- ✅ Non-destructive SSL certificate handling
- ✅ Graceful Keycloak startup with public-client fallback
- ✅ Shell completions (Bash, Zsh, Fish, PowerShell)
- ✅ Environment management with `.fastman` config
- ✅ `install:cert` merged CA bundle command
- ✅ Ruff replaced black/isort/autoflake
- ✅ 44 tests (unit + integration)
