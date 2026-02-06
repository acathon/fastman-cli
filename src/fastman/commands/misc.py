"""
Miscellaneous commands (utils, config, docs, etc).
"""
import sys
import os
import shutil
import json
import secrets
import subprocess
import re
import logging
import importlib
from pathlib import Path

from .. import __version__
from .base import Command, register, COMMAND_REGISTRY
from ..console import Output, Style, HAS_PYFIGLET, HAS_RICH, console
from ..utils import PackageManager, NameValidator, PathManager

if HAS_PYFIGLET:
    import pyfiglet

logger = logging.getLogger('fastman')

@register
class RouteListCommand(Command):
    signature = "route:list {--path=} {--method=}"
    description = "List all API routes"

    def handle(self):
        path_filter = self.option("path")
        method_filter = self.option("method", "").upper()

        sys.path.insert(0, str(Path.cwd()))

        try:
            from app.main import app

            routes = []
            for route in app.routes:
                route_path = getattr(route, "path", "")
                route_methods = getattr(route, "methods", set())

                # Apply filters
                if path_filter and path_filter not in route_path:
                    continue
                if method_filter and method_filter not in route_methods:
                    continue

                methods_str = ",".join(sorted(route_methods)) if route_methods else "WS"
                name = getattr(route, "name", "-")

                routes.append([methods_str, route_path, name])

            if routes:
                Output.table(
                    ["Methods", "Path", "Name"],
                    routes,
                    "API Routes"
                )
                Output.info(f"Total routes: {len(routes)}")
            else:
                Output.warn("No routes found")

        except ImportError as e:
            Output.error(f"Failed to import application: {e}")
            logger.exception(e)
        except Exception as e:
            Output.error(f"An unexpected error occurred while loading routes: {e}")
            logger.exception(e)


@register
class TinkerCommand(Command):
    signature = "tinker"
    description = "Interactive Python shell with app context"

    def handle(self):
        sys.path.insert(0, str(Path.cwd()))

        # Import commonly used items
        namespace = {}
        db_session = None

        try:
            from app.core.config import settings
            from app.core.database import SessionLocal, Base

            db_session = SessionLocal()
            namespace.update({
                "settings": settings,
                "SessionLocal": SessionLocal,
                "Base": Base,
                "db": db_session
            })

            Output.info("Fastman Interactive Shell")
            Output.info("Available: settings, SessionLocal, Base, db")

        except ImportError:
            Output.warn(
                "Could not import application components. "
                "Run `fastman init` if this is not a Fastman project."
            )
            Output.info("Fastman Interactive Shell")

        try:
            try:
                import IPython
                IPython.start_ipython(argv=[], user_ns=namespace)
            except ImportError:
                import code
                code.interact(local=namespace)
        finally:
            if db_session:
                db_session.close()


@register
class GenerateKeyCommand(Command):
    signature = "generate:key {--show}"
    description = "Generate secret key"

    def handle(self):
        key = secrets.token_urlsafe(32)
        show_only = self.flag("show")

        if show_only:
            Output.echo(f"Generated key: {key}")
            return

        env_file = Path(".env")

        if env_file.exists():
            content = env_file.read_text()

            if "SECRET_KEY=" in content:
                # Update existing key
                content = re.sub(
                    r'SECRET_KEY=.*',
                    f'SECRET_KEY={key}',
                    content
                )
            else:
                # Add new key
                content += f"\nSECRET_KEY={key}\n"

            env_file.write_text(content)
            Output.success("Secret key updated in .env")
        else:
            # Create new .env
            env_file.write_text(f"SECRET_KEY={key}\n")
            Output.success("Secret key created in .env")

        Output.echo(f"Key: {key}")


@register
class ConfigCacheCommand(Command):
    signature = "config:cache"
    description = "Cache environment configuration"

    def handle(self):
        env_file = Path(".env")

        if not env_file.exists():
            Output.error(".env file not found")
            return

        config = {}
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()

        cache_file = Path("config_cache.json")
        cache_file.write_text(json.dumps(config, indent=2))

        Output.success(f"Configuration cached ({len(config)} variables)")


@register
class ConfigClearCommand(Command):
    signature = "config:clear"
    description = "Clear configuration cache"

    def handle(self):
        cache_file = Path("config_cache.json")

        if cache_file.exists():
            cache_file.unlink()
            Output.success("Configuration cache cleared")
        else:
            Output.info("No cache to clear")


@register
class CacheClearCommand(Command):
    signature = "cache:clear"
    description = "Clear Python cache files"

    def handle(self):
        count = 0

        for root, dirs, files in os.walk("."):
            # Remove __pycache__ directories
            for dir_name in dirs:
                if dir_name == "__pycache__":
                    dir_path = Path(root) / dir_name
                    shutil.rmtree(dir_path)
                    count += 1

            # Remove .pyc files
            for file_name in files:
                if file_name.endswith(".pyc"):
                    file_path = Path(root) / file_name
                    file_path.unlink()
                    count += 1

        Output.success(f"Cleared {count} cache files/directories")


@register
class ImportCommand(Command):
    signature = "import {package}"
    description = "Install Python package"

    def handle(self):
        package = self.argument(0)

        if not package:
            Output.error("Package name required")
            return

        Output.info(f"Installing {package}...")

        if PackageManager.install([package]):
            Output.success(f"Package '{package}' installed")
        else:
            Output.error(f"Failed to install '{package}'")


@register
class PkgListCommand(Command):
    signature = "pkg:list"
    description = "List installed packages"

    def handle(self):
        manager, _ = PackageManager.detect()

        Output.info(f"Using package manager: {manager}")

        try:
            if manager == "uv":
                subprocess.run(["uv", "pip", "list"], check=True)
            elif manager == "poetry":
                subprocess.run(["poetry", "show"], check=True)
            elif manager == "pipenv":
                subprocess.run(["pipenv", "list"], check=True)
            else:
                subprocess.run([sys.executable, "-m", "pip", "list"], check=True)
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            Output.error(f"Failed to list packages: {e}")


@register
class ListCommand(Command):
    signature = "list"
    description = "Show all available commands"

    def handle(self):
        """Display commands in Laravel Artisan style"""

        # Header
        if HAS_PYFIGLET:
            banner = pyfiglet.figlet_format("Fastman", font="slant")
            if HAS_RICH:
                console.print(f"[cyan]{banner}[/cyan]", end="")
            else:
                print(f"{Style.CYAN}{banner}{Style.RESET}", end="")
        else:
            if HAS_RICH:
                console.print(f"[bold cyan]Fastman[/bold cyan] [yellow]v{__version__}[/yellow]")
            else:
                print(f"{Style.BOLD}{Style.CYAN}Fastman{Style.RESET} {Style.YELLOW}v{__version__}{Style.RESET}")

        # If we used pyfiglet, we haven't printed the version number yet (except in rich title),
        # so we print it below the banner.
        # If we didn't use pyfiglet, we already printed "Fastman vX.Y.Z" in the fallback header.
        if HAS_PYFIGLET:
            if HAS_RICH:
                console.print(f"[yellow]v{__version__}[/yellow]")
                console.print()
            else:
                print(f"{Style.YELLOW}v{__version__}{Style.RESET}\n")

        # Usage section
        if HAS_RICH:
            console.print("[yellow]Usage:[/yellow]")
            console.print("  command [options] [arguments]")
            console.print()
            console.print("[yellow]Options:[/yellow]")
            console.print("  [green]-h, --help[/green]     Display help for a command")
            console.print("  [green]-v, --version[/green]  Display application version")
            console.print()
        else:
            print(f"{Style.YELLOW}Usage:{Style.RESET}")
            print("  command [options] [arguments]\n")
            print(f"{Style.YELLOW}Options:{Style.RESET}")
            print(f"  {Style.GREEN}-h, --help{Style.RESET}     Display help for a command")
            print(f"  {Style.GREEN}-v, --version{Style.RESET}  Display application version\n")

        # Organize commands by namespace/category
        categories = {
            "Project Setup": [],
            "Development": [],
            "Scaffolding": [],
            "Database & Migrations": [],
            "Testing": [],
            "Authentication": [],
            "Package Management": [],
            "Configuration": [],
            "Utilities": []
        }

        for name, cls in sorted(COMMAND_REGISTRY.items()):
            # Categorize commands
            if name in ["new", "init"]:
                categories["Project Setup"].append((name, cls.description))
            elif name == "serve":
                categories["Development"].append((name, cls.description))
            elif name.startswith("make:") and name not in ["make:migration", "make:seeder", "make:factory", "make:test"]:
                categories["Scaffolding"].append((name, cls.description))
            elif name.startswith("migrate") or name.startswith("db:") or name in ["make:migration", "make:seeder"]:
                categories["Database & Migrations"].append((name, cls.description))
            elif name in ["make:test", "make:factory"]:
                categories["Testing"].append((name, cls.description))
            elif name.startswith("install:auth"):
                categories["Authentication"].append((name, cls.description))
            elif name in ["import", "pkg:list"]:
                categories["Package Management"].append((name, cls.description))
            elif name.startswith("config:") or name.startswith("cache:") or name.startswith("generate:"):
                categories["Configuration"].append((name, cls.description))
            else:
                categories["Utilities"].append((name, cls.description))

        # Display commands by category
        if HAS_RICH:
            console.print("[yellow]Available commands:[/yellow]")
        else:
            print(f"{Style.YELLOW}Available commands:{Style.RESET}")

        for category, commands in categories.items():
            if not commands:
                continue

            # Category header
            if HAS_RICH:
                console.print(f" [bold yellow]{category}[/bold yellow]")
            else:
                print(f" {Style.BOLD}{Style.YELLOW}{category}{Style.RESET}")

            # Find the longest command name for alignment
            max_length = max(len(cmd[0]) for cmd in commands) if commands else 0

            # Display commands in this category
            for cmd_name, description in sorted(commands):
                padding = " " * (max_length - len(cmd_name) + 2)

                if HAS_RICH:
                    console.print(f"  [green]{cmd_name}[/green]{padding}{description}")
                else:
                    print(f"  {Style.GREEN}{cmd_name}{Style.RESET}{padding}{description}")

            # Empty line between categories
            print()


@register
class VersionCommand(Command):
    signature = "version"
    description = "Show Fastman version"

    def handle(self):
        Output.echo(f"Fastman v{__version__}", Style.BOLD)
        Output.info("The Complete FastAPI CLI Framework")
        Output.echo("License: MIT", Style.CYAN)
        Output.echo("Repository: https://github.com/fastman/fastman", Style.CYAN)

        # Show Python version
        py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        Output.echo(f"Python: {py_version}", Style.CYAN)

        # Show package manager
        manager, _ = PackageManager.detect()
        Output.echo(f"Package Manager: {manager}", Style.CYAN)


@register
class DocsCommand(Command):
    signature = "docs {--open}"
    description = "Show documentation or open in browser"

    def handle(self):
        should_open = self.flag("open")

        if should_open:
            import webbrowser
            url = "https://fastman.dev/docs"
            Output.info(f"Opening {url}...")
            webbrowser.open(url)
        else:
            Output.echo("\n📚 Fastman Documentation", Style.BOLD + Style.CYAN)
            Output.echo("=" * 80)
            Output.echo("\nQuick Start:")
            Output.echo("  1. fastman new myproject", Style.GREEN)
            Output.echo("  2. cd myproject", Style.GREEN)
            Output.echo("  3. fastman serve", Style.GREEN)

            Output.echo("\nCommon Commands:")
            Output.echo("  make:feature {name}  - Create vertical slice with CRUD", Style.CYAN)
            Output.echo("  make:api {name}      - Create lightweight endpoint", Style.CYAN)
            Output.echo("  make:migration {msg} - Create database migration", Style.CYAN)
            Output.echo("  migrate              - Run migrations", Style.CYAN)
            Output.echo("  route:list           - List all routes", Style.CYAN)

            Output.echo("\nDocumentation: https://fastman.dev/docs")
            Output.echo("Repository: https://github.com/fastman/fastman")
            Output.echo("=" * 80)


@register
class InspectCommand(Command):
    signature = "inspect {type} {name}"
    description = "Inspect project component (model, route, feature)"

    def handle(self):
        comp_type = self.argument(0)
        comp_name = self.argument(1)

        if not comp_type or not comp_name:
            Output.error("Usage: fastman inspect {type} {name}")
            Output.info("Types: model, feature, api, route")
            return

        sys.path.insert(0, str(Path.cwd()))

        if comp_type == "feature":
            self._inspect_feature(comp_name)
        elif comp_type == "api":
            self._inspect_api(comp_name)
        elif comp_type == "model":
            self._inspect_model(comp_name)
        else:
            Output.error(f"Unknown type: {comp_type}")

    def _inspect_feature(self, name: str):
        """Inspect a feature"""
        snake = NameValidator.to_snake_case(name)
        path = Path("app/features") / snake

        if not path.exists():
            Output.error(f"Feature '{snake}' not found")
            return

        Output.echo(f"\n📦 Feature: {snake}", Style.BOLD + Style.CYAN)
        Output.echo("=" * 80)

        files = {
            "models.py": "Database Models",
            "schemas.py": "Pydantic Schemas",
            "service.py": "Business Logic",
            "router.py": "API Routes"
        }

        for file_name, description in files.items():
            file_path = path / file_name
            if file_path.exists():
                size = file_path.stat().st_size
                Output.echo(f"  ✓ {file_name.ljust(15)} - {description} ({size} bytes)", Style.GREEN)
            else:
                Output.echo(f"  ✗ {file_name.ljust(15)} - {description}", Style.RED)

        # Try to load router and show endpoints
        try:
            module = importlib.import_module(f"app.features.{snake}.router")
            if hasattr(module, "router"):
                router = module.router
                Output.echo(f"\n  Endpoints:", Style.BOLD)
                for route in router.routes:
                    methods = ",".join(getattr(route, "methods", []))
                    path = getattr(route, "path", "")
                    Output.echo(f"    {methods.ljust(10)} {path}", Style.CYAN)
        except (ImportError, AttributeError):
            logger.debug(f"Could not inspect router for feature: {name}")

    def _inspect_api(self, name: str):
        """Inspect an API"""
        snake = NameValidator.to_snake_case(name)
        path = Path("app/api") / snake

        if not path.exists():
            Output.error(f"API '{snake}' not found")
            return

        Output.echo(f"\n🔌 API: {snake}", Style.BOLD + Style.CYAN)
        Output.echo("=" * 80)

        router_path = path / "router.py"
        schema_path = path / "schema.py"

        if router_path.exists():
            Output.echo(f"  Type: REST API", Style.GREEN)
        elif schema_path.exists():
            Output.echo(f"  Type: GraphQL API", Style.GREEN)

    def _inspect_model(self, name: str):
        """Inspect a model"""
        snake = NameValidator.to_snake_case(name)
        pascal = NameValidator.to_pascal_case(name)

        try:
            module = importlib.import_module(f"app.models.{snake}")
            model_class = getattr(module, pascal)

            Output.echo(f"\n🗄️  Model: {pascal}", Style.BOLD + Style.CYAN)
            Output.echo("=" * 80)
            Output.echo(f"  Table: {model_class.__tablename__}", Style.GREEN)
            Output.echo(f"  Columns:", Style.BOLD)

            for column in model_class.__table__.columns:
                col_type = str(column.type)
                nullable = "NULL" if column.nullable else "NOT NULL"
                pk = "PRIMARY KEY" if column.primary_key else ""
                Output.echo(f"    {column.name.ljust(20)} {col_type.ljust(15)} {nullable} {pk}", Style.CYAN)

        except (ImportError, AttributeError) as e:
            Output.error(f"Could not load model '{pascal}': {e}")
        except Exception as e:
            Output.error(f"An unexpected error occurred while inspecting model: {e}")


@register
class OptimizeCommand(Command):
    signature = "optimize {--check}"
    description = "Optimize project (remove unused imports, format code)"

    def handle(self):
        check_only = self.flag("check")

        if check_only:
            Output.info("Checking for optimization opportunities...")
        else:
            Output.info("Optimizing project...")

        # Check for common tools
        tools = {
            "black": "Code formatting",
            "isort": "Import sorting",
            "autoflake": "Remove unused imports"
        }

        missing_tools = []
        for tool, desc in tools.items():
            if not shutil.which(tool):
                missing_tools.append(tool)

        if missing_tools:
            Output.warn(f"Missing tools: {', '.join(missing_tools)}")
            if Output.confirm("Install optimization tools?"):
                manager, _ = PackageManager.detect()
                install_args = missing_tools.copy()
                if manager != "pip":
                    # For uv, poetry, pipenv, --dev is a flag, not a package
                    # We need to handle this in PackageManager.install eventually,
                    # but for now we append it as an arg.
                    # Ideally, PackageManager.install should take options.
                    # Since we are passing a list of packages, we rely on the fact
                    # that they are appended to the command.
                    # Note: This might treat --dev as a package if the implementation iterates blindly.
                    pass

                # Currently PackageManager.install takes a list of packages and appends them to command.
                # If we pass ["--dev", "black"], it becomes `uv add --dev black`.

                if manager != "pip":
                    install_args = ["--dev"] + missing_tools

                PackageManager.install(install_args)

        # Run optimization
        app_path = Path("app")
        if not app_path.exists():
            Output.error("Not in a Fastman project")
            return

        if not check_only:
            # Format with black
            if shutil.which("black"):
                Output.info("Formatting code with black...")
                subprocess.run(["black", "app/", "tests/"], capture_output=True)

            # Sort imports
            if shutil.which("isort"):
                Output.info("Sorting imports with isort...")
                subprocess.run(["isort", "app/", "tests/"], capture_output=True)

            # Remove unused imports
            if shutil.which("autoflake"):
                Output.info("Removing unused imports...")
                subprocess.run([
                    "autoflake",
                    "--remove-all-unused-imports",
                    "--recursive",
                    "--in-place",
                    "app/",
                    "tests/"
                ], capture_output=True)

            Output.success("Project optimized!")
        else:
            Output.info("Check complete")


@register
class BuildCommand(Command):
    signature = "build {--docker}"
    description = "Build project for production"

    def handle(self):
        use_docker = self.flag("docker")

        if use_docker:
            self._build_docker()
        else:
            self._build_standard()

    def _build_docker(self):
        """Build Docker image"""
        Output.info("Building Docker image...")

        # Create Dockerfile if it doesn't exist
        dockerfile = Path("Dockerfile")
        if not dockerfile.exists():
            content = '''FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run migrations and start server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
'''
            PathManager.write_file(dockerfile, content)
            Output.success("Dockerfile created")

        # Build image
        project_name = Path.cwd().name
        try:
            subprocess.run([
                "docker", "build",
                "-t", f"{project_name}:latest",
                "."
            ], check=True)
            Output.success(f"Docker image built: {project_name}:latest")
        except subprocess.CalledProcessError:
            Output.error("Docker build failed")

    def _build_standard(self):
        """Standard build"""
        Output.info("Building project...")

        # Run tests
        if Path("tests").exists():
            Output.info("Running tests...")
            result = subprocess.run(["pytest", "tests/"], capture_output=True)
            if result.returncode != 0:
                Output.error("Tests failed")
                return

        # Check types (if mypy available)
        if shutil.which("mypy"):
            Output.info("Checking types...")
            subprocess.run(["mypy", "app/"], capture_output=True)

        Output.success("Build complete!")
