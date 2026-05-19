"""
Miscellaneous commands (utils, config, docs, etc).
"""
import json
import logging
import os
import re
import secrets
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

from .. import __codename__, __version__
from ..console import HAS_PYFIGLET, HAS_RICH, Output, Style, console
from ..utils import EnvManager, PackageManager, PathManager
from .base import COMMAND_REGISTRY, Command, register

if HAS_PYFIGLET:
    import pyfiglet

logger = logging.getLogger('fastman')

@register
class RouteListCommand(Command):
    signature = "route:list {--path=} {--method=} {--json}"
    description = "List all API routes"
    help = """
Examples:
  fastman route:list
  fastman route:list --path=/users
  fastman route:list --method=POST
  fastman route:list --path=/api/v1 --method=GET
  fastman route:list --json                 # machine-readable output

Imports app/main.py and walks app.routes. If imports fail (missing
deps in venv), falls back to running a subprocess in the project's env.

The --json output is suitable for piping to jq, importing into
editors, or feeding into CI scripts that check for expected routes:

  fastman route:list --json | jq '.[] | select(.methods | contains(["POST"]))'
"""

    def handle(self):
        path_filter = self.option("path")
        method_filter = self.option("method", "").upper()
        as_json = self.flag("json")

        cwd_path = str(Path.cwd())
        path_added = cwd_path not in sys.path
        if path_added:
            sys.path.insert(0, cwd_path)

        routes = []

        try:
            try:
                from app.main import app
                routes = self._get_routes_from_app(app)
            except ImportError:
                # Fallback to subprocess if fastman is running in isolated environment
                try:
                    routes = self._get_routes_via_subprocess()
                except Exception as e:
                    if as_json:
                        # Even on error, emit valid JSON so tooling can parse it.
                        print(json.dumps({"error": str(e)}))
                        sys.exit(1)
                    Output.error(f"Failed to load routes: {e}")
                    return
            except Exception as e:
                if as_json:
                    print(json.dumps({"error": str(e)}))
                    sys.exit(1)
                Output.error(f"An unexpected error occurred while loading routes: {e}")
                logger.exception(e)
                return
        finally:
            # Clean up sys.path to avoid pollution
            if path_added and cwd_path in sys.path:
                sys.path.remove(cwd_path)

        # Filter
        filtered_routes = []
        for methods_str, route_path, name in routes:
            if path_filter and path_filter not in route_path:
                continue
            if method_filter and method_filter not in methods_str:
                continue
            filtered_routes.append([methods_str, route_path, name])

        # JSON output path — print nothing else to stdout. Tooling-friendly.
        if as_json:
            payload = [
                {
                    "methods": (
                        ["WS"] if methods_str == "WS"
                        else methods_str.split(",")
                    ),
                    "path": route_path,
                    "name": name,
                }
                for methods_str, route_path, name in filtered_routes
            ]
            print(json.dumps(payload, indent=2))
            return

        if filtered_routes:
            Output.table(
                ["Methods", "Path", "Name"],
                filtered_routes,
                "API Routes"
            )
            Output.info(f"Total routes: {len(filtered_routes)}")
        else:
            Output.warn("No routes found")

    def _get_routes_from_app(self, app):
        """Extract routes from loaded app instance"""
        routes = []
        for route in app.routes:
            route_path = getattr(route, "path", "")
            route_methods = getattr(route, "methods", set())

            methods_str = ",".join(sorted(route_methods)) if route_methods else "WS"
            name = getattr(route, "name", "-")

            routes.append([methods_str, route_path, name])
        return routes

    def _get_routes_via_subprocess(self):
        """Get routes by running inline Python in the project environment"""
        # Use a unique marker to identify the JSON output
        marker = "__FASTMAN_ROUTES_JSON__"
        script_content = f'''
import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path.cwd()))

try:
    from app.main import app
    routes_data = []
    for route in app.routes:
        route_path = getattr(route, "path", "")
        route_methods = getattr(route, "methods", set())
        methods_str = ",".join(sorted(route_methods)) if route_methods else "WS"
        name = getattr(route, "name", "-")
        routes_data.append([methods_str, route_path, name])
    print("{marker}" + json.dumps(routes_data) + "{marker}")
except Exception as e:
    print("{marker}" + json.dumps(dict(error=str(e))) + "{marker}")
    sys.exit(1)
'''
        try:
            manager_prefix = PackageManager.get_run_prefix()
            if manager_prefix:
                cmd = manager_prefix + ["python", "-c", script_content]
            else:
                cmd = ["python", "-c", script_content]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=60
            )

            # Extract JSON from output using our marker
            stdout = result.stdout
            json_data = None
            
            if marker in stdout:
                # Find the JSON between the markers
                parts = stdout.split(marker)
                if len(parts) >= 3:
                    json_str = parts[1]
                    try:
                        json_data = json.loads(json_str)
                    except json.JSONDecodeError as e:
                        raise Exception(f"Failed to parse routes JSON: {e}")
            
            if result.returncode != 0:
                # Check if we got an error in the JSON
                if json_data and isinstance(json_data, dict) and "error" in json_data:
                    raise Exception(json_data["error"])
                
                error_msg = result.stderr or "Unknown error in subprocess"
                if "email-validator is not installed" in error_msg:
                    raise Exception("email-validator is not installed, run `pip install 'pydantic[email]'`")

                raise Exception(error_msg)

            if json_data is None:
                # Fallback: try direct parsing for backward compatibility
                try:
                    json_data = json.loads(stdout)
                except json.JSONDecodeError:
                    # Try to extract JSON from stdout (look for array/object)
                    for i, char in enumerate(stdout):
                        if char in '[{':
                            try:
                                json_data = json.loads(stdout[i:])
                                break
                            except json.JSONDecodeError:
                                continue
                    
                    if json_data is None:
                        raise Exception(f"Could not parse routes output. Raw output: {stdout[:200]}")
            
            return json_data

        except subprocess.TimeoutExpired:
            raise Exception("Route list command timed out")


@register
class TinkerCommand(Command):
    signature = "tinker"
    description = "Interactive Python shell with app context"
    help = """
Examples:
  fastman tinker

Starts an IPython REPL (or stdlib `code` fallback) with `settings`,
`db`, `SessionLocal`, and `Base` pre-imported. Best for ad-hoc DB
queries and inspecting app state.
"""

    def handle(self):
        cwd = Path.cwd()
        sys.path.insert(0, str(cwd))

        # Activate the project's .venv site-packages if present
        venv_path = cwd / ".venv"
        if venv_path.exists():
            if sys.platform == "win32":
                site_packages = venv_path / "Lib" / "site-packages"
            else:
                # Find the python version directory under lib
                lib_path = venv_path / "lib"
                py_dirs = sorted(lib_path.glob("python*")) if lib_path.exists() else []
                site_packages = py_dirs[0] / "site-packages" if py_dirs else lib_path / "site-packages"

            if site_packages.exists():
                site_str = str(site_packages)
                if site_str not in sys.path:
                    sys.path.insert(1, site_str)

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
    signature = "config:appkey {--show}"
    description = "Generate secret key"
    help = """
Examples:
  fastman config:appkey            Generate + write to all .env files
  fastman config:appkey --show     Print to terminal only

Uses secrets.token_urlsafe(32). Writes to .env, .env.develop, and
.env.staging by default.
"""

    def handle(self):
        key = secrets.token_urlsafe(32)
        show_only = self.flag("show")

        if show_only:
            Output.echo(f"Generated key: {key}")
            return

        env_files = [Path(f) for f in EnvManager.ENV_FILES]
        updated = False

        for env_file in env_files:
            if env_file.exists():
                content = env_file.read_text(encoding='utf-8')

                if "SECRET_KEY=" in content:
                    content = re.sub(
                        r'SECRET_KEY=.*',
                        f'SECRET_KEY={key}',
                        content
                    )
                else:
                    content += f"\nSECRET_KEY={key}\n"

                env_file.write_text(content, encoding='utf-8')
                updated = True

        if updated:
            Output.success("Secret key updated in all env files")
        else:
            env_file = Path(".env")
            env_file.write_text(f"SECRET_KEY={key}\n", encoding='utf-8')
            Output.success("Secret key created in .env")

        Output.echo(f"Key: {key}")


@register
class CacheClearCommand(Command):
    signature = "cache:clear"
    description = "Clear Python cache files"
    help = """
Examples:
  fastman cache:clear

Recursively removes __pycache__/ and *.pyc files. Use after pulling
upstream changes if you see stale import errors.
"""

    def handle(self):
        # Collect paths first, then delete (avoid modifying dirs during iteration)
        pycache_dirs = []
        pyc_files = []
        
        for root, dirs, files in os.walk("."):
            for dir_name in dirs[:]:
                if dir_name == "__pycache__":
                    pycache_dirs.append(Path(root) / dir_name)
                    dirs.remove(dir_name)  # Don't descend into __pycache__
            
            for file_name in files:
                if file_name.endswith(".pyc"):
                    pyc_files.append(Path(root) / file_name)
        
        count = 0
        for dir_path in pycache_dirs:
            try:
                shutil.rmtree(dir_path)
                count += 1
            except (PermissionError, OSError) as e:
                Output.warn(f"Could not remove {dir_path}: {e}")
        
        for file_path in pyc_files:
            try:
                file_path.unlink()
                count += 1
            except (PermissionError, OSError) as e:
                Output.warn(f"Could not remove {file_path}: {e}")

        Output.success(f"Cleared {count} cache files/directories")


@register
class ListCommand(Command):
    signature = "list"
    description = "Show all available commands"
    help = """
Examples:
  fastman list       Show all commands grouped by category
  fastman            Same as above (default when no args)

Categories are ordered by user frequency: Project, Development,
Scaffolding, Database, Integrations, ...
"""

    def handle(self):
        """Display commands grouped by namespace category"""

        # Header
        if HAS_PYFIGLET:
            banner = pyfiglet.figlet_format("Fastman", font="slant")
            if HAS_RICH:
                console.print(f"[cyan]{banner}[/cyan]", end="")
            else:
                print(f"{Style.CYAN}{banner}{Style.RESET}", end="")
        else:
            if HAS_RICH:
                console.print(f"[bold cyan]Fastman[/bold cyan] [yellow]v{__version__}[/yellow] [dim]({__codename__})[/dim]")
            else:
                print(f"{Style.BOLD}{Style.CYAN}Fastman{Style.RESET} {Style.YELLOW}v{__version__}{Style.RESET} {Style.DIM}({__codename__}){Style.RESET}")

        # If we used pyfiglet, we haven't printed the version number yet (except in rich title),
        # so we print it below the banner.
        # If we didn't use pyfiglet, we already printed "Fastman vX.Y.Z" in the fallback header.
        if HAS_PYFIGLET:
            if HAS_RICH:
                console.print(f"[yellow]v{__version__}[/yellow] [dim]({__codename__})[/dim]")
                console.print()
            else:
                print(f"{Style.YELLOW}v{__version__}{Style.RESET} {Style.DIM}({__codename__}){Style.RESET}\n")

        # Usage section
        if HAS_RICH:
            console.print("[yellow]Usage:[/yellow]")
            console.print("  command [options] [arguments]")
            console.print()
            console.print("[yellow]Global Options:[/yellow]")
            console.print("  [green]-h, --help[/green]            Display help for a command")
            console.print("  [green]-v, --version[/green]         Display application version")
            console.print("  [green]-n, --no-interaction[/green]  Never prompt; fail fast if input is required (CI-friendly)")
            console.print()
        else:
            print(f"{Style.YELLOW}Usage:{Style.RESET}")
            print("  command [options] [arguments]\n")
            print(f"{Style.YELLOW}Global Options:{Style.RESET}")
            print(f"  {Style.GREEN}-h, --help{Style.RESET}            Display help for a command")
            print(f"  {Style.GREEN}-v, --version{Style.RESET}         Display application version")
            print(f"  {Style.GREEN}-n, --no-interaction{Style.RESET}  Never prompt; fail fast if input is required\n")

        # Organize commands by namespace/category.
        # Order matters — these render top-to-bottom in the order listed,
        # roughly by user frequency (project setup first, polish last).
        categories: dict[str, list] = {
            "Project": [],
            "Development": [],
            "Scaffolding": [],
            "Database": [],
            "Integrations": [],
            "Routes": [],
            "Packages": [],
            "Testing": [],
            "Configuration": [],
            "Cache": [],
            "Utilities": [],
        }

        for name, cls in sorted(COMMAND_REGISTRY.items()):
            if name in ["create", "init"]:
                categories["Project"].append((name, cls.description))
            elif name in ["serve", "build", "optimize", "tinker"]:
                categories["Development"].append((name, cls.description))
            elif name.startswith("make:") and name not in [
                "make:migration", "make:seeder", "make:factory", "make:test", "make:mail",
            ]:
                categories["Scaffolding"].append((name, cls.description))
            elif name == "route:list":
                categories["Routes"].append((name, cls.description))
            elif (
                name.startswith("database:")
                or name.startswith("migrate")
                or name in ["make:migration", "make:seeder"]
            ):
                categories["Database"].append((name, cls.description))
            elif name in ["make:test", "make:factory"]:
                categories["Testing"].append((name, cls.description))
            elif (
                name.startswith("install:")
                or name == "make:mail"
            ):
                categories["Integrations"].append((name, cls.description))
            elif name.startswith("package:"):
                categories["Packages"].append((name, cls.description))
            elif name.startswith("config:"):
                categories["Configuration"].append((name, cls.description))
            elif name.startswith("cache:"):
                categories["Cache"].append((name, cls.description))
            else:
                # version / list / docs / completion / activate / env / about
                categories["Utilities"].append((name, cls.description))

        # Compute a single global column width so every command name aligns
        # across categories — one tidy column across the screen.
        all_names = [cmd[0] for cmds in categories.values() for cmd in cmds]
        column_width = max(len(n) for n in all_names) if all_names else 0

        if HAS_RICH:
            console.print("[yellow]Available commands:[/yellow]")
            console.print()
        else:
            print(f"{Style.YELLOW}Available commands:{Style.RESET}\n")

        for category, commands in categories.items():
            if not commands:
                continue

            # Category header with count, e.g. "Scaffolding  (12)"
            count = f"({len(commands)})"
            if HAS_RICH:
                console.print(f" [bold yellow]{category}[/bold yellow] [dim]{count}[/dim]")
            else:
                print(f" {Style.BOLD}{Style.YELLOW}{category}{Style.RESET} {Style.DIM}{count}{Style.RESET}")

            for cmd_name, description in sorted(commands):
                padding = " " * (column_width - len(cmd_name) + 2)
                if HAS_RICH:
                    console.print(
                        f"  [green]{cmd_name}[/green]{padding}"
                        f"[dim]{description}[/dim]"
                    )
                else:
                    print(f"  {Style.GREEN}{cmd_name}{Style.RESET}{padding}{description}")

            print()


@register
class VersionCommand(Command):
    signature = "version"
    description = "Show Fastman version"
    help = """
Examples:
  fastman version    Terse: version, Python, package manager
  fastman -v         Alias

For a fuller diagnostic (env, stack, integrations, routes), use:
  fastman about
"""

    def handle(self):
        Output.echo(f"Fastman v{__version__} ({__codename__})", Style.BOLD)
        Output.info("The Complete FastAPI CLI Framework")
        Output.echo("License: MIT", Style.CYAN)
        Output.echo("Repository: https://github.com/acathon/fastman-cli", Style.CYAN)

        # Show Python version
        py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        Output.echo(f"Python: {py_version}", Style.CYAN)

        # Show package manager
        manager, _ = PackageManager.detect()
        Output.echo(f"Package Manager: {manager}", Style.CYAN)


@register
class AboutCommand(Command):
    """Full project & environment diagnostic in one screen.

    Designed to be the first command a teammate runs in an unfamiliar
    project: "what is this thing built on, and what state is it in?"
    One-screen project diagnostic.
    """

    signature = "about"
    description = "Show project, runtime, and integration diagnostics"
    help = """
Run anywhere — sections that don't apply are simply skipped. Useful as the
first thing a new teammate runs on a freshly cloned project, or as a
support-ticket attachment when something feels off.

Examples:
  fastman about
"""

    def handle(self):
        import platform
        from ..utils import FastmanConfig

        in_project = Path("app").is_dir() or Path(".fastmanrc").exists()
        config = FastmanConfig.read()

        # ── Fastman / runtime section ──────────────────────────────────
        self._section("Fastman")
        self._row("Version", f"{__version__} ({__codename__})")
        self._row("Python", platform.python_version())
        self._row("Platform", f"{platform.system()} {platform.release()}")

        # ── Project section (only if we're in one) ─────────────────────
        if in_project:
            self._section("Project")
            self._row("Pattern", config.get("pattern") or self._infer_pattern() or "—")
            manager, _ = PackageManager.detect()
            self._row("Package Manager", manager)
            self._row("Database", config.get("database") or self._infer_database() or "—")
            self._row("Project Root", str(Path.cwd().resolve()))
            self._row("Active Env File", self._active_env() or "—")

        # ── Stack section ──────────────────────────────────────────────
        stack = self._collect_stack_versions()
        if stack:
            self._section("Stack")
            for name, version in stack:
                self._row(name, version)

        # ── Integrations section ───────────────────────────────────────
        if in_project:
            integrations = self._detect_integrations()
            if integrations:
                self._section("Integrations")
                for name, value in integrations:
                    self._row(name, value)

        # ── Routes (best-effort — only if app/main.py imports cleanly) ─
        if in_project:
            route_count = self._count_routes()
            if route_count is not None:
                self._section("Routes")
                self._row("Total Routes", str(route_count))

        Output.new_line()

    # ── Section / row primitives ────────────────────────────────────────

    def _section(self, title: str) -> None:
        """Print a section header. Renders using Rich when available."""
        from ..console import HAS_RICH, console
        if HAS_RICH:
            console.print()
            console.print(f"[bold cyan]{title}[/bold cyan]")
            console.print(f"[dim]{'─' * 60}[/dim]")
        else:
            print()
            print(f"{Style.BOLD}{Style.CYAN}{title}{Style.RESET}")
            print("─" * 60)

    def _row(self, label: str, value: str) -> None:
        from ..console import HAS_RICH, console
        if HAS_RICH:
            console.print(f"  [dim]{label:<20}[/dim] [highlight]{value}[/highlight]")
        else:
            print(f"  {label:<20} {value}")

    # ── Data collection ────────────────────────────────────────────────

    def _infer_pattern(self) -> Optional[str]:
        """Fallback when .fastmanrc is missing (older projects)."""
        if Path("app/features").is_dir():
            return "feature"
        if Path("app/controllers").is_dir():
            return "layer"
        if Path("app/api").is_dir():
            return "api"
        return None

    def _infer_database(self) -> Optional[str]:
        """Detect database driver from generated app/core/."""
        if Path("app/core/firebase.py").is_file():
            return "firebase"
        db_file = Path("app/core/database.py")
        if not db_file.is_file():
            return None
        content = db_file.read_text(encoding="utf-8")
        for driver, marker in (
            ("postgresql", "postgresql"),
            ("mysql", "pymysql"),
            ("oracle", "oracledb"),
            ("sqlite", "sqlite"),
        ):
            if marker in content.lower():
                return driver
        return None

    def _active_env(self) -> Optional[str]:
        """Mirror serve's env resolution priority."""
        env = os.environ.get("ENVIRONMENT", "develop")
        if env == "production" and Path(".env").exists():
            return ".env"
        if Path(f".env.{env}").exists():
            return f".env.{env}"
        if Path(".env.develop").exists():
            return ".env.develop"
        if Path(".env").exists():
            return ".env"
        return None

    def _collect_stack_versions(self) -> list:
        """Pull versions from installed packages — silently skip what's missing."""
        from importlib.metadata import PackageNotFoundError, version
        rows = []
        for label, dist in (
            ("FastAPI", "fastapi"),
            ("SQLAlchemy", "sqlalchemy"),
            ("Pydantic", "pydantic"),
            ("Pydantic-Settings", "pydantic-settings"),
            ("Alembic", "alembic"),
            ("Uvicorn", "uvicorn"),
            ("FastAPI-Mail", "fastapi-mail"),
        ):
            try:
                rows.append((label, version(dist)))
            except PackageNotFoundError:
                continue
        return rows

    def _detect_integrations(self) -> list:
        """Detect optional integrations from filesystem traces."""
        rows = []

        # Auth — keycloak puts file in app/core/, others in app/features/auth/
        if Path("app/core/keycloak.py").is_file():
            rows.append(("Auth Provider", "keycloak"))
        elif Path("app/features/auth").is_dir():
            # Distinguish JWT / OAuth / Passkey by what files exist
            auth = Path("app/features/auth")
            if (auth / "security.py").is_file():
                rows.append(("Auth Provider", "jwt"))
            elif (auth / "oauth_config.py").is_file():
                rows.append(("Auth Provider", "oauth"))
            elif any((auth / f).is_file() for f in ["passkey.py", "webauthn.py"]):
                rows.append(("Auth Provider", "passkey"))
            else:
                rows.append(("Auth Provider", "auth (custom)"))

        # Mail
        if Path("app/core/mail.py").is_file():
            rows.append(("Mail Transport", "fastapi-mail"))

        # Certificates
        certs = Path("certs")
        if certs.is_dir():
            cert_count = sum(
                1 for f in certs.iterdir()
                if f.is_file() and f.suffix in (".pem", ".crt")
            )
            if cert_count:
                rows.append(("Certificates", f"{certs}/ ({cert_count} file{'s' if cert_count != 1 else ''})"))

        # GraphQL
        if Path("app/core/graphql.py").is_file():
            rows.append(("GraphQL", "strawberry-graphql"))

        return rows

    def _count_routes(self) -> Optional[int]:
        """Best-effort route count. Returns None if app can't be imported here."""
        cwd_str = str(Path.cwd())
        added = cwd_str not in sys.path
        if added:
            sys.path.insert(0, cwd_str)
        try:
            try:
                from app.main import app  # type: ignore
                return len(app.routes)
            except Exception:
                return None
        finally:
            if added and cwd_str in sys.path:
                sys.path.remove(cwd_str)


@register
class DocsCommand(Command):
    signature = "docs {--open}"
    description = "Show documentation or open in browser"
    help = """
Examples:
  fastman docs           Print quick-reference inline
  fastman docs --open    Open the docs website in your browser
"""

    def handle(self):
        should_open = self.flag("open")

        if should_open:
            import webbrowser
            url = "https://acathon.github.io/fastman-cli/"
            Output.info(f"Opening {url}...")
            webbrowser.open(url)
        else:
            Output.echo("\n📚 Fastman Documentation", Style.BOLD + Style.CYAN)
            Output.echo("=" * 80)
            Output.echo("\nQuick Start:")
            Output.echo("  1. fastman create myproject", Style.GREEN)
            Output.echo("  2. cd myproject", Style.GREEN)
            Output.echo("  3. fastman serve", Style.GREEN)

            Output.echo("\nCommon Commands:")
            Output.echo("  make:feature {name}    - Create vertical slice with CRUD", Style.CYAN)
            Output.echo("  make:api {name}        - Create lightweight endpoint", Style.CYAN)
            Output.echo("  make:migration {msg}   - Create database migration", Style.CYAN)
            Output.echo("  database:migrate       - Run migrations", Style.CYAN)
            Output.echo("  route:list             - List all routes", Style.CYAN)

            Output.echo("\nDocumentation: https://acathon.github.io/fastman-cli/")
            Output.echo("Repository: https://github.com/acathon/fastman-cli")
            Output.echo("=" * 80)


@register
class OptimizeCommand(Command):
    signature = "optimize {--check}"
    description = "Optimize project (lint, format, fix imports)"
    help = """
Examples:
  fastman optimize           Format and fix in place
  fastman optimize --check   Check without modifying (CI-friendly)

Runs `ruff check --fix` then `ruff format` on app/ and tests/. Offers
to install ruff via your detected package manager if missing.
"""

    def handle(self):
        check_only = self.flag("check")

        if check_only:
            Output.info("Checking for optimization opportunities...")
        else:
            Output.info("Optimizing project...")

        if not shutil.which("ruff"):
            Output.warn("Ruff is not installed")
            if Output.confirm("Install ruff?"):
                manager, _ = PackageManager.detect()
                try:
                    if manager == "uv":
                        subprocess.run(["uv", "add", "--dev", "ruff"], check=True, timeout=300)
                    elif manager == "poetry":
                        subprocess.run(["poetry", "add", "--group", "dev", "ruff"], check=True, timeout=300)
                    elif manager == "pipenv":
                        subprocess.run(["pipenv", "install", "--dev", "ruff"], check=True, timeout=300)
                    else:
                        PackageManager.install(["ruff"])
                    Output.success("Ruff installed")
                except subprocess.CalledProcessError as e:
                    Output.error(f"Failed to install ruff: {e}")
                    return
                except subprocess.TimeoutExpired:
                    Output.error("Installation timed out")
                    return
            else:
                return

        app_path = Path("app")
        if not app_path.exists():
            Output.error("Not in a Fastman project")
            return

        if not check_only:
            Output.info("Fixing imports and lint issues...")
            subprocess.run(
                ["python", "-m", "ruff", "check", "--fix", "app/", "tests/"],
                capture_output=True, timeout=120,
            )

            Output.info("Formatting code...")
            subprocess.run(
                ["python", "-m", "ruff", "format", "app/", "tests/"],
                capture_output=True, timeout=120,
            )

            Output.success("Project optimized!")
        else:
            subprocess.run(
                ["python", "-m", "ruff", "check", "app/", "tests/"],
                timeout=120,
            )
            subprocess.run(
                ["python", "-m", "ruff", "format", "--check", "app/", "tests/"],
                timeout=120,
            )


@register
class BuildCommand(Command):
    signature = "build {--docker}"
    description = "Build project for production"
    help = """
Examples:
  fastman build              Runs tests + mypy as a green-check sanity pass
  fastman build --docker     Builds a Docker image (generates Dockerfile if missing)

The non-Docker mode is the \"is everything green?\" check you'd run before
pushing. The Docker mode tags the image as <project_name>:latest.
"""

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
CMD ["sh", "-c", "python -m alembic upgrade head && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"]
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
            result = subprocess.run(["python", "-m", "pytest", "tests/"], capture_output=True)
            if result.returncode != 0:
                Output.error("Tests failed")
                return

        # Check types (if mypy available)
        if shutil.which("mypy"):
            Output.info("Checking types...")
            subprocess.run(["python", "-m", "mypy", "app/"], capture_output=True)

        Output.success("Build complete!")


@register
class CompletionCommand(Command):
    """Generate shell completion scripts"""
    signature = "completion {shell} {--install}"
    description = "Generate shell completion script (bash, zsh, fish, powershell)"
    help = """
Examples:
  fastman completion bash                Print the script to stdout
  fastman completion bash --install      Save + wire into ~/.bashrc
  fastman completion zsh --install
  fastman completion fish --install
  fastman completion powershell --install

Completions are generated dynamically from COMMAND_REGISTRY, so newly
added commands show up automatically with no edits to this file.
"""

    def handle(self):
        shell = self.argument(0, "bash").lower()
        install = self.flag("install")
        
        from ..shell_completion import ShellCompletion, get_completion_install_instructions
        
        generators = {
            "bash": ShellCompletion.generate_bash,
            "zsh": ShellCompletion.generate_zsh,
            "fish": ShellCompletion.generate_fish,
            "powershell": ShellCompletion.generate_powershell,
            "ps": ShellCompletion.generate_powershell,
        }
        
        if shell not in generators:
            Output.error(f"Unknown shell: {shell}")
            Output.info("Supported shells: bash, zsh, fish, powershell")
            return
        
        # Generate completion script
        completion_script = generators[shell]()
        
        if install:
            # Install to appropriate location
            self._install_completion(shell, completion_script)
        else:
            # Just print the script
            print(completion_script)
            
            Output.new_line()
            Output.info("To install this completion script, run:")
            Output.highlight(f"  fastman completion {shell} --install")
            Output.new_line()
            Output.info("Or save it manually and source it in your shell profile")
    
    def _install_completion(self, shell: str, script: str):
        """Install completion script to appropriate location"""
        home = Path.home()
        
        if shell in ["bash"]:
            target = home / ".fastman-completion.bash"
            profile_file = home / ".bashrc"
            source_line = f"source {target}"
            
        elif shell in ["zsh"]:
            completions_dir = home / ".zsh" / "completions"
            completions_dir.mkdir(parents=True, exist_ok=True)
            target = completions_dir / "_fastman"
            profile_file = home / ".zshrc"
            source_line = None  # zsh finds it automatically via fpath
            
        elif shell in ["fish"]:
            completions_dir = home / ".config" / "fish" / "completions"
            completions_dir.mkdir(parents=True, exist_ok=True)
            target = completions_dir / "fastman.fish"
            profile_file = None
            source_line = None
            
        elif shell in ["powershell", "ps"]:
            target = home / "fastman-completion.ps1"
            profile_file = None
            source_line = f". {target}"
            
        else:
            Output.error(f"Installation not supported for {shell}")
            return
        
        # Write completion script
        target.write_text(script)
        Output.success(f"Completion script installed to: {target}")
        
        # Update profile if needed
        if profile_file and source_line:
            if profile_file.exists():
                content = profile_file.read_text()
                if source_line not in content:
                    with open(profile_file, "a") as f:
                        f.write(f"\n# Fastman CLI completion\n{source_line}\n")
                    Output.success(f"Updated {profile_file}")
            else:
                profile_file.write_text(f"# Fastman CLI completion\n{source_line}\n")
                Output.success(f"Created {profile_file}")
        
        Output.new_line()
        Output.info("Please restart your shell or run:")
        if shell == "bash":
            Output.highlight("  source ~/.bashrc")
        elif shell == "zsh":
            Output.highlight("  source ~/.zshrc")
        elif shell == "fish":
            Output.highlight("  source ~/.config/fish/completions/fastman.fish")
        elif shell == "powershell":
            Output.highlight(f"  . {target}")


@register
class ActivateCommand(Command):
    """Detect and display virtual environment activation command"""
    signature = "activate {--create-script}"
    description = "Show virtual environment activation command"
    help = """
Examples:
  fastman activate                     Print the activation command for your shell
  fastman activate --create-script     Drop activate.sh / activate.bat helper

Detects .venv/, venv/, or env/ in the cwd. Detects shell via $SHELL.
"""

    help = """
Examples:
  fastman route:list
  fastman route:list --path=/users
  fastman route:list --method=POST
  fastman route:list --path=/api/v1 --method=GET

Imports app/main.py and walks app.routes. If imports fail (missing
dependencies in venv), falls back to running a subprocess in the
project's environment.
"""
    help = """
Examples:
  fastman tinker

Starts an IPython REPL (or stdlib fallback) with , ,
, and  pre-imported. Best for ad-hoc database
queries and inspecting app state.
"""
    help = """
Examples:
  fastman config:appkey            Generate + write to all .env files
  fastman config:appkey --show     Print to terminal only

Generates a cryptographically secure key via secrets.token_urlsafe(32).
Writes to .env, .env.develop, and .env.staging by default.
"""
    help = """
Examples:
  fastman cache:clear

Recursively removes __pycache__/ and *.pyc files. Use after pulling
upstream changes if you see stale import errors.
"""
    help = """
Examples:
  fastman optimize           Format and fix
  fastman optimize --check   Check without modifying (CI-friendly)

Runs ruff check --fix + ruff format on app/ and tests/. Offers to
install ruff if missing.
"""
    help = """
Examples:
  fastman build              Runs tests then mypy
  fastman build --docker     Builds a Docker image instead

The non-Docker mode is a CI-style "is everything green?" check.
The Docker mode generates a Dockerfile if missing.
"""
    help = """
Examples:
  fastman completion bash               Print the script to stdout
  fastman completion bash --install     Save + wire into ~/.bashrc
  fastman completion zsh --install
  fastman completion fish --install
  fastman completion powershell --install

Completions are generated dynamically from the registered command list,
so newly added commands show up automatically.
"""
    help = """
Examples:
  fastman activate                     Show the activation command
  fastman activate --create-script     Drop activate.bat/.sh helper

Detects .venv/, venv/, or env/ in cwd and prints the right command
for your shell.
"""
    help = """
Examples:
  fastman docs           Print quick-reference inline
  fastman docs --open    Open the docs website in your browser
"""
    help = """
Examples:
  fastman list           Show all available commands grouped by category
  fastman                Same as fastman list

Categories order by user frequency: Project, Development, Scaffolding,
Database, Integrations, ...
"""
    help = """
Examples:
  fastman version    Terse: version, Python, package manager
  fastman -v         Alias

For a fuller diagnostic (env, stack, integrations, routes), use:
  fastman about
"""
    def handle(self):
        """Detect venv and display activation command"""
        cwd = Path.cwd()
        
        # Common venv locations
        venv_paths = [
            cwd / ".venv",
            cwd / "venv",
            cwd / "env",
        ]
        
        # Find existing venv
        venv_path = None
        for path in venv_paths:
            if path.exists():
                venv_path = path
                break
        
        if not venv_path:
            Output.error("No virtual environment found")
            Output.info("Expected one of: .venv, venv, env")
            Output.info("Run 'fastman create' to create a new project with venv")
            return
        
        # Detect OS
        is_windows = os.name == 'nt'
        
        # Detect shell (Unix only)
        shell = os.environ.get('SHELL', '').split('/')[-1] if not is_windows else 'cmd'
        
        Output.section("Virtual Environment Detected", str(venv_path))
        
        if is_windows:
            # Windows
            activate_cmd = f"{venv_path}\\Scripts\\activate.bat"
            activate_ps = f"{venv_path}\\Scripts\\Activate.ps1"
            
            Output.info("Windows detected")
            Output.new_line()
            Output.highlight("Command Prompt (cmd.exe):")
            Output.echo(f"  {activate_cmd}")
            Output.new_line()
            Output.highlight("PowerShell:")
            Output.echo(f"  {activate_ps}")
            
        else:
            # Unix-like
            activate_path = venv_path / "bin" / "activate"
            
            if shell in ['fish']:
                activate_cmd = f"source {activate_path}.fish"
            elif shell in ['csh', 'tcsh']:
                activate_cmd = f"source {activate_path}.csh"
            else:
                # bash, zsh, sh, etc.
                activate_cmd = f"source {activate_path}"
            
            Output.info(f"Shell detected: {shell}")
            Output.new_line()
            Output.highlight("Activation command:")
            Output.echo(f"  {activate_cmd}")
            
            # Also show how to deactivate
            Output.new_line()
            Output.comment("To deactivate, run: deactivate")
        
        Output.new_line()
        Output.info("Copy and paste the command above to activate your environment")
        
        # Optional: Create activation helper script
        if self.flag("create-script"):
            self._create_activation_script(venv_path, is_windows)
    
    def _create_activation_script(self, venv_path: Path, is_windows: bool):
        """Create a helper script for activation"""
        if is_windows:
            script_path = Path("activate.bat")
            content = f"@echo off\n call {venv_path}\\Scripts\\activate.bat"
        else:
            script_path = Path("activate.sh")
            content = f"#!/bin/bash\n source {venv_path}/bin/activate"
        
        PathManager.write_file(script_path, content)
        
        if not is_windows:
            # Make executable on Unix
            os.chmod(script_path, 0o755)
        
        Output.success(f"Created {script_path}")
        Output.info(f"Run: ./{script_path}")

