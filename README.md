# Fastman - The Complete FastAPI CLI Framework

![Fastman Logo](docs/static/img/fastman-logo.jpg)

Fastman is a Laravel-inspired CLI tool for FastAPI. It eliminates boilerplate fatigue by generating project structures, handling database migrations, and scaffolding features, models, and middleware instantly.

Whether you prefer Vertical Slice (Feature) architecture or Layered architecture, Fastman sets it up for you in seconds.

## Features

- **Zero-Dependency Core**: Runs with standard library (Rich/Pyfiglet optional for UI)
- **Smart Package Detection**: Automatically uses uv, poetry, pipenv, or pip
- **Multiple Architectures**: Supports feature (default), api, and layer patterns
- **Database Ready**: First-class support for SQLite, PostgreSQL, MySQL, Oracle, and Firebase
- **Interactive Shell**: Includes a tinker command to interact with your app context
- **Auth Scaffolding**: One-command JWT or Keycloak authentication setup
- **Extensible**: Create custom CLI commands with `make:command`

## Quick Start

### Installation

Install Fastman from PyPI:

```bash
pip install fastman
```

Or with uv (recommended):

```bash
uv pip install fastman
```

### Create a New Project

Generate a new API with a specific architecture and package manager:

```bash
# Default (Feature pattern + UV + SQLite)
fastman new my-project

# Layered architecture with PostgreSQL and Poetry
fastman new blog_api --pattern=layer --database=postgresql --package=poetry

# Minimal project setup
fastman new minimal_api --minimal
```

### Run the Development Server

```bash
cd my-project
fastman serve
```

Visit http://127.0.0.1:8000/docs to see your API documentation.

## Project Architectures

Fastman supports three directory structures out of the box:

### 1. Feature Pattern (Default)
Best for domain-driven design and vertical slices. Code is organized by "what it does" rather than "what it is."

```plaintext
app/
├── features/
│   └── auth/           # Router, Service, Models, Schemas all in one place
├── api/                # Simple endpoints
└── core/               # Shared config
```

### 2. Layer Pattern
Traditional MVC-style architecture.

```plaintext
app/
├── controllers/
├── services/
├── repositories/
├── models/
└── schemas/
```

### 3. API Pattern
Lightweight structure for simple microservices.

```plaintext
app/
├── api/
├── schemas/
└── models/
```

## Command Reference

### Project Setup

#### `new` - Create a new FastAPI project
```bash
fastman new {name} [--minimal] [--pattern=feature] [--package=uv] [--database=sqlite]
```

Create a new FastAPI project with your preferred architecture and database.

**Options:**
- `--minimal` - Create minimal project structure
- `--pattern` - Architecture pattern: `feature` (default), `layer`, or `api`
- `--package` - Package manager: `uv` (default), `poetry`, or `pipenv`
- `--database` - Database: `sqlite` (default), `postgresql`, `mysql`, `oracle`, or `firebase`

**Examples:**
```bash
# Feature-based project with PostgreSQL
fastman new blog --pattern=feature --database=postgresql

# Layered project with MySQL
fastman new ecommerce --pattern=layer --database=mysql --package=poetry

# Minimal API with Firebase
fastman new notifications --minimal --database=firebase
```

#### `init` - Initialize Fastman in existing project
```bash
fastman init
```

Add Fastman support to an existing FastAPI project. This creates the necessary directory structure and configuration files.

---

### Development Server

#### `serve` - Start development server
```bash
fastman serve [--host=127.0.0.1] [--port=8000] [--reload]
```

Start the Uvicorn development server with hot reload enabled by default.

**Options:**
- `--host` - Host address (default: 127.0.0.1)
- `--port` - Port number (default: 8000)
- `--reload` - Enable auto-reload (enabled by default)

**Examples:**
```bash
# Start on default port
fastman serve

# Start on custom host and port
fastman serve --host=0.0.0.0 --port=3000
```

---

### Scaffolding - Features & APIs

#### `make:feature` - Create a vertical slice feature
```bash
fastman make:feature {name} [--crud]
```

Create a complete vertical slice feature with router, service, model, and schema files.

**Options:**
- `--crud` - Generate CRUD endpoints (Create, Read, Update, Delete)

**Examples:**
```bash
# Create basic feature
fastman make:feature posts

# Create feature with full CRUD
fastman make:feature users --crud
```

#### `make:api` - Create a lightweight API endpoint
```bash
fastman make:api {name} [--style=rest]
```

Create a lightweight API endpoint for simpler use cases.

**Options:**
- `--style` - API style: `rest` (default) or `graphql`

**Examples:**
```bash
# REST API
fastman make:api products

# GraphQL API
fastman make:api search --style=graphql
```

#### `make:websocket` - Create WebSocket endpoint
```bash
fastman make:websocket {name}
```

Create a WebSocket endpoint with connection manager for real-time communication.

**Example:**
```bash
fastman make:websocket chat
```

#### `make:controller` - Create a controller class
```bash
fastman make:controller {name}
```

Create a controller class for handling HTTP requests (useful in layered architecture).

**Example:**
```bash
fastman make:controller UserController
```

---

### Scaffolding - Components

#### `make:model` - Create database model
```bash
fastman make:model {name} [--table=]
```

Create a SQLAlchemy model for database operations.

**Options:**
- `--table` - Specify custom table name

**Examples:**
```bash
# Model with auto-generated table name
fastman make:model User

# Model with custom table name
fastman make:model BlogPost --table=posts
```

#### `make:service` - Create service class
```bash
fastman make:service {name}
```

Create a service class for business logic layer.

**Example:**
```bash
fastman make:service EmailService
```

#### `make:repository` - Create repository class
```bash
fastman make:repository {name}
```

Create a repository pattern class for data access abstraction.

**Example:**
```bash
fastman make:repository UserRepository
```

#### `make:middleware` - Create HTTP middleware
```bash
fastman make:middleware {name}
```

Create a FastAPI middleware for request/response processing.

**Example:**
```bash
fastman make:middleware LoggingMiddleware
```

#### `make:dependency` - Create FastAPI dependency
```bash
fastman make:dependency {name}
```

Create a FastAPI dependency for dependency injection.

**Example:**
```bash
fastman make:dependency get_current_user
```

#### `make:exception` - Create custom exception
```bash
fastman make:exception {name}
```

Create a custom exception class for error handling.

**Example:**
```bash
fastman make:exception ValidationException
```

#### `make:command` - Create custom CLI command
```bash
fastman make:command {name}
```

Create a custom Fastman CLI command for your project-specific needs.

**Example:**
```bash
fastman make:command ProcessPayments
```

This generates a command template in `app/console/commands/` that you can customize. Your custom commands are automatically loaded by Fastman.

#### `make:test` - Create test file
```bash
fastman make:test {name}
```

Create a pytest test file with boilerplate code.

**Example:**
```bash
fastman make:test test_users
```

---

### Database & Migrations

#### `make:migration` - Create database migration
```bash
fastman make:migration {message}
```

Create a new Alembic migration file.

**Example:**
```bash
fastman make:migration "add users table"
```

#### `migrate` - Run database migrations
```bash
fastman migrate
```

Run all pending database migrations.

#### `migrate:rollback` - Rollback migrations
```bash
fastman migrate:rollback [--steps=1]
```

Rollback the last N migrations.

**Options:**
- `--steps` - Number of migrations to rollback (default: 1)

**Example:**
```bash
# Rollback last migration
fastman migrate:rollback

# Rollback last 3 migrations
fastman migrate:rollback --steps=3
```

#### `migrate:reset` - Reset database
```bash
fastman migrate:reset
```

Rollback all migrations (reset database to initial state).

#### `migrate:status` - Show migration status
```bash
fastman migrate:status
```

Display the current status of all migrations.

#### `make:seeder` - Create database seeder
```bash
fastman make:seeder {name}
```

Create a database seeder for populating test data.

**Example:**
```bash
fastman make:seeder UsersSeeder
```

#### `db:seed` - Run database seeders
```bash
fastman db:seed [--class=]
```

Run database seeders to populate your database with test data.

**Options:**
- `--class` - Run specific seeder class

**Examples:**
```bash
# Run all seeders
fastman db:seed

# Run specific seeder
fastman db:seed --class=UsersSeeder
```

---

### Testing & Factories

#### `make:test` - Create test file
```bash
fastman make:test {name}
```

Create a pytest test file with standard boilerplate.

**Example:**
```bash
fastman make:test test_authentication
```

#### `make:factory` - Create model factory
```bash
fastman make:factory {name}
```

Create a model factory for generating test data.

**Example:**
```bash
fastman make:factory UserFactory
```

---

### Authentication

#### `install:auth` - Install authentication scaffolding
```bash
fastman install:auth [--type=jwt] [--provider=]
```

Scaffold complete authentication system with login, registration, and user management.

**Options:**
- `--type` - Authentication type: `jwt` (default), `oauth`, or `keycloak`
- `--provider` - OAuth provider (for OAuth type): `google`, `github`, etc.

**Examples:**
```bash
# Install JWT authentication
fastman install:auth

# Install OAuth with Google
fastman install:auth --type=oauth --provider=google

# Install Keycloak integration
fastman install:auth --type=keycloak
```

This generates:
- `app/features/auth/` (Router, Service, Schemas)
- JWT/OAuth handling utilities
- User model and migration
- Login/Register/Me endpoints

---

### Package Management

#### `import` - Install Python package
```bash
fastman import {package}
```

Install a Python package using the detected package manager.

**Example:**
```bash
fastman import requests
```

#### `pkg:list` - List installed packages
```bash
fastman pkg:list
```

Display all installed Python packages in the project.

---

### Utilities & Tools

#### `tinker` - Interactive Python shell
```bash
fastman tinker
```

Open an interactive Python shell with your app context loaded (settings, database session, models).

**Example:**
```bash
$ fastman tinker

Fastman Interactive Shell
Available: settings, SessionLocal, Base, db

>>> user = db.query(User).first()
>>> print(user.email)
admin@example.com
```

#### `route:list` - List all API routes
```bash
fastman route:list [--path=] [--method=]
```

Display a table of all registered API routes.

**Options:**
- `--path` - Filter by path pattern
- `--method` - Filter by HTTP method (GET, POST, etc.)

**Examples:**
```bash
# List all routes
fastman route:list

# Filter by path
fastman route:list --path=/api/users

# Filter by method
fastman route:list --method=POST
```

#### `inspect` - Inspect project component
```bash
fastman inspect {type} {name}
```

Inspect a specific component (model, route, feature) in your project.

**Example:**
```bash
fastman inspect model User
fastman inspect route /api/users
fastman inspect feature auth
```

#### `generate:key` - Generate secret key
```bash
fastman generate:key [--show]
```

Generate a secure secret key for your application.

**Options:**
- `--show` - Display the key in terminal

**Example:**
```bash
fastman generate:key --show
```

#### `config:cache` - Cache configuration
```bash
fastman config:cache
```

Cache the environment configuration for faster loading.

#### `config:clear` - Clear configuration cache
```bash
fastman config:clear
```

Clear the cached configuration.

#### `cache:clear` - Clear Python cache
```bash
fastman cache:clear
```

Remove all Python `__pycache__` directories and `.pyc` files.

#### `optimize` - Optimize project code
```bash
fastman optimize [--check]
```

Format code, sort imports, and remove unused variables.

**Options:**
- `--check` - Check only without making changes

**Example:**
```bash
# Optimize and fix
fastman optimize

# Check without changes
fastman optimize --check
```

#### `build` - Build for production
```bash
fastman build [--docker]
```

Build the project for production deployment.

**Options:**
- `--docker` - Generate Dockerfile and docker-compose.yml

**Examples:**
```bash
# Standard build
fastman build

# Build with Docker configuration
fastman build --docker
```

#### `docs` - Show documentation
```bash
fastman docs [--open]
```

Display Fastman documentation or open it in browser.

**Options:**
- `--open` - Open documentation in web browser

#### `list` - Show all commands
```bash
fastman list
```

Display a list of all available Fastman commands with descriptions.

#### `version` - Show Fastman version
```bash
fastman version
```

Display the currently installed Fastman version.

---

## Advanced Usage

### Custom Commands

Create project-specific CLI commands:

```bash
# Generate custom command
fastman make:command SendEmails

# Edit the generated file
# app/console/commands/send_emails_command.py
```

Your custom command structure:

```python
from fastman import Command, register

@register
class SendEmailsCommand(Command):
    signature = "emails:send {--queue}"
    description = "Send pending emails"
    
    def handle(self):
        queue = self.flag("queue")
        # Your logic here
        self.info("Emails sent!")
```

Run it with:
```bash
fastman emails:send --queue
```

### Repository Pattern

For clean architecture, use the repository pattern:

```bash
# Create repository
fastman make:repository UserRepository

# Create service that uses it
fastman make:service UserService
```

### Testing Workflow

Complete testing setup:

```bash
# Create factories for test data
fastman make:factory UserFactory
fastman make:factory PostFactory

# Create test file
fastman make:test test_posts

# Create seeders for development
fastman make:seeder DevelopmentSeeder

# Run seeders
fastman db:seed
```

## Configuration

Fastman automatically detects your project setup:

- **Package Manager**: uv, poetry, pipenv, or pip
- **Database**: From `DATABASE_URL` in settings
- **Project Pattern**: From directory structure

All commands respect your project's configuration.

## Best Practices

1. **Use Feature Pattern** for domain-driven apps with complex business logic
2. **Use Layer Pattern** for traditional MVC-style applications
3. **Use API Pattern** for simple microservices
4. **Always run migrations** after creating models
5. **Use seeders** for development data, **factories** for testing
6. **Create custom commands** for repetitive tasks
7. **Use repositories** for clean separation of data access logic

## Integration Tips

### With Docker

```bash
# Generate Docker configuration
fastman build --docker

# Files created: Dockerfile, docker-compose.yml
```

### With CI/CD

```bash
# In your pipeline
fastman migrate              # Run migrations
fastman optimize --check     # Lint check
fastman build               # Production build
```

### With Testing

```bash
# Setup test database
fastman db:seed --class=TestSeeder

# Run tests with pytest
pytest tests/
```

## Troubleshooting

**Command not found**: Ensure Fastman is installed in your active environment:
```bash
pip install --upgrade fastman
```

**Package manager not detected**: Explicitly specify when creating projects:
```bash
fastman new myapp --package=poetry
```

**Migration errors**: Check your database connection string in `.env` or settings.

**Custom commands not loading**: Ensure they're in `app/console/commands/` and use the `@register` decorator.

## Contributing

Fastman is open source! Contributions are welcome.

Repository: https://github.com/fastman/fastman

## License

This project is licensed under the **Apache License 2.0**.

## Support

- **Documentation**: Run `fastman docs --open`
- **Issues**: https://github.com/fastman/fastman/issues
- **Discussions**: https://github.com/fastman/fastman/discussions

---

**Happy building with Fastman! 🚀**
