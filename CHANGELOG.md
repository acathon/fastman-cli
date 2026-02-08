# Changelog

All notable changes to Fastman will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-02-07

### ✨ Added

#### Professional Console UI
- **New Output Methods**: `section()`, `task()`, `file_created()`, `directory_created()`, `next_steps()`, `listing()`, `line()`, `highlight()`, `comment()`
- **Interactive Prompts**: `ask()`, `choice()` for user input
- **Progress Indicators**: `progress()` context manager and `spinner()` for long operations
- **Enhanced Tables**: Professional table output with rounded corners and styled headers
- **Better Banners**: Multiple font fallbacks (slant → big → standard → chunky) with double-line borders
- **Status Indicators**: Color-coded task progress (yellow for in-progress, green for done)

#### Shell Completions
- **Bash Completion**: Full command and option completion with value suggestions
- **Zsh Completion**: Native zsh completion with descriptions and argument hints
- **Fish Completion**: Fish shell completion script
- **PowerShell Completion**: Windows PowerShell completion support
- **New Command**: `fastman completion {shell} --install` for one-liner installation

#### Virtual Environment Management
- **New Command**: `fastman activate` - Detects and shows correct venv activation command
- **OS Detection**: Automatically detects Windows/Unix and shows appropriate commands
- **Shell Detection**: Detects bash/zsh/fish and shows correct syntax
- **Helper Script Generation**: `--create-script` flag to generate activation helper

#### Integration Tests
- **29 Comprehensive Tests**: Real filesystem operations (not mocks)
- **Project Creation Tests**: Verify directory structure, files, and content
- **Scaffold Tests**: Test feature generation and validation
- **Utility Tests**: PathManager, NameValidator integration tests
- **Template Tests**: Template rendering verification
- **CLI Tests**: Command context and main CLI functionality

### 🔧 Fixed

#### Critical Bugs
- **pyproject.toml Syntax**: Removed stray closing bracket that caused parse errors
- **Subprocess Timeouts**: Added timeout handling to all subprocess calls (30s-300s depending on operation)
- **CLI Option Parsing**: Fixed `option()` method to handle both `--name=value` and `--name value` formats
- **File Operation Errors**: Enhanced error handling with specific exceptions (PermissionError, IsADirectoryError)

#### Improvements
- **Better Error Messages**: More descriptive error messages with context
- **Path Validation**: Enhanced path traversal protection
- **File Existence Checks**: Better handling of existing files/directories
- **Package Installation**: Timeout protection for pip/poetry/pipenv/uv installations

### 🎨 Changed

#### UI/UX Improvements
- **Project Creation Output**: Now shows banner, sections, file creation messages, and formatted next steps
- **Feature Creation Output**: Shows files created as a formatted list with endpoints table
- **Task Progress**: All package manager operations now show progress indicators
- **Success Messages**: More celebratory and informative success messages

#### Code Quality
- **Type Hints**: Improved type annotations throughout
- **Documentation**: Added comprehensive docstrings
- **Error Handling**: Consistent error handling patterns
- **Logging**: Better integration with Python logging

### 🗑️ Deprecated

- None

### 🛡️ Security

- **Path Traversal**: Enhanced protection against path traversal attacks
- **Input Validation**: Stricter validation for identifiers and paths
- **Secret Generation**: Using `secrets.token_urlsafe()` for secure key generation

---

## [0.1.0] - 2026-01-XX

### ✨ Added

#### Core Features
- **Project Creation**: `fastman new` with support for feature/api/layer patterns
- **Multiple Package Managers**: Auto-detection of uv, poetry, pipenv, pip
- **Database Support**: SQLite, PostgreSQL, MySQL, Oracle, Firebase
- **Architecture Patterns**: Feature-based, API-focused, and Layered architectures

#### Scaffolding Commands
- `make:feature` - Create vertical slice features
- `make:api` - Create API endpoints
- `make:model` - Create SQLAlchemy models
- `make:service` - Create service classes
- `make:controller` - Create controllers
- `make:middleware` - Create middleware
- `make:schema` - Create Pydantic schemas
- `make:test` - Create test files
- `make:seeder` - Create database seeders
- `make:factory` - Create model factories
- `make:repository` - Create repositories
- `make:command` - Create custom CLI commands
- `make:exception` - Create custom exceptions
- `make:dependency` - Create FastAPI dependencies
- `make:websocket` - Create WebSocket endpoints

#### Database Commands
- `make:migration` - Create Alembic migrations
- `migrate` - Run migrations
- `migrate:rollback` - Rollback migrations
- `migrate:reset` - Reset all migrations
- `migrate:status` - Check migration status
- `db:seed` - Run database seeders

#### Development Tools
- `serve` - Start development server with auto-reload
- `tinker` - Interactive Python shell with DB session
- `route:list` - List all API routes
- `generate:key` - Generate secret keys
- `config:cache` - Cache configuration
- `config:clear` - Clear config cache
- `cache:clear` - Clear application cache

#### Utilities
- `list` - Show all available commands (Artisan-style)
- `version` - Show version information
- `docs` - Open documentation
- `inspect` - Inspect code components
- `optimize` - Optimize code (black/isort/autoflake)
- `build` - Build Docker image
- `import` - Import data from files
- `pkg:list` - List installed packages

#### Authentication
- `install:auth` - Install authentication system (JWT, OAuth, Keycloak)

#### Technical Features
- **Smart Package Detection**: Automatically detects package manager from lock files
- **Zero-Dependency Core**: Runs with standard library (Rich/Pyfiglet optional)
- **Console Output**: Rich integration with ANSI fallback
- **Logging**: Integrated Python logging
- **Command Registry**: Extensible command system
- **Template Engine**: Simple variable substitution for code generation

---

## Release Notes Format

### Types of Changes

- `✨ Added` - New features
- `🔧 Fixed` - Bug fixes
- `🎨 Changed` - Changes to existing functionality
- `🗑️ Deprecated` - Soon-to-be removed features
- `🗑️ Removed` - Removed features
- `🛡️ Security` - Security improvements
- `📚 Documentation` - Documentation updates

---

[Unreleased]: https://github.com/acathon/fastman-cli/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/acathon/fastman-cli/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/acathon/fastman-cli/releases/tag/v0.1.0
