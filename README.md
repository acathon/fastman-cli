<div align="center">

![Fastman Logo](docs/static/img/fastman-logo.jpg)

# Fastman

### The Complete FastAPI CLI Framework

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Linting](https://img.shields.io/badge/linting-ruff-261230)](https://github.com/astral-sh/ruff)
[![Version](https://img.shields.io/badge/version-0.4.2-orange.svg)](https://test.pypi.org/project/fastman/)

**Eliminate boilerplate. Ship faster.**

[Documentation](https://acathon.github.io/fastman-cli) · [TestPyPI](https://test.pypi.org/project/fastman/) · [Contributing](CONTRIBUTING.md)

</div>

---

## How to install

Fastman is currently in **beta** on TestPyPI:

```bash
pip install -i https://test.pypi.org/simple/ fastman
```

Or from source:

```bash
git clone https://github.com/acathon/fastman-cli.git
cd fastman-cli
pip install -e .
```

---

## Quick Start

```bash
# Create a new project
fastman create my-api --pattern=feature --database=sqlite

cd my-api

# Start development server
fastman serve

# Scaffold a complete CRUD feature
fastman make:feature users --crud

# Create and run a migration
fastman make:migration "create users table"
fastman database:migrate
```

Visit `http://localhost:8000/docs` to see your API.

---

## What You Get

| Category | Commands |
|----------|----------|
| **Project** | `create`, `init`, `serve`, `activate`, `tinker`, `about`, `update` |
| **Scaffolding** | `make:feature`, `make:model`, `make:api`, `make:controller`, `make:service`, `make:repository`, `make:middleware`, `make:seeder`, `make:factory`, `make:command`, `make:test` |
| **Database** | `make:migration`, `database:migrate`, `migrate:rollback`, `migrate:status`, `database:seed`, `db:fresh`, `model:show` |
| **Install** | `install:auth --type=jwt\|oauth\|keycloak\|passkey`, `install:mail`, `install:cert` |
| **Utilities** | `config:appkey`, `optimize`, `route:list --json`, `build --docker`, `env`, `completion`, `docs` |

### Architecture Patterns

```bash
fastman create my-api --pattern=feature   # Vertical slices (default)
fastman create my-api --pattern=api       # API-focused
fastman create my-api --pattern=layer     # Layered architecture
```

### Authentication (one command)

```bash
fastman install:auth --type=jwt           # JWT with /register, /login, /me
fastman install:auth --type=oauth --provider=google
fastman install:auth --type=keycloak      # FastAPIKeycloak + /me + Swagger auth
fastman install:auth --type=passkey       # WebAuthn / biometric
```

### Smart Defaults

- Auto-detects `uv`, `poetry`, `pipenv`, or `pip`
- Shell completions for Bash, Zsh, Fish, PowerShell
- SQLite, PostgreSQL, MySQL, Oracle, Firebase support
- Ruff for linting and formatting
- Merged certificate bundle support for private CAs

---

## Documentation

Full documentation is available at **[acathon.github.io/fastman-cli](https://acathon.github.io/fastman-cli)**.

Covers installation, architecture concepts, every command in detail, authentication guides, deployment, and more.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
git clone https://github.com/acathon/fastman-cli.git
cd fastman-cli
pip install -e ".[dev]"
pytest
```

---

## License

MIT — see [LICENSE](LICENSE).

---

<div align="center">

**[Documentation](https://acathon.github.io/fastman-cli)** · **[Report Bug](https://github.com/acathon/fastman-cli/issues)** · **[Request Feature](https://github.com/acathon/fastman-cli/issues)**

</div>
