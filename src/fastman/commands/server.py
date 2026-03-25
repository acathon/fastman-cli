"""Server commands."""
import json
import os
import subprocess
from pathlib import Path
from .base import Command, register
from ..console import Output, Style
from ..utils import PackageManager

FASTMAN_CONFIG = Path(".fastman")

# Planned .fastman config keys (wire up in next version):
# {
#   "env": "production",          # active env file (implemented)
#   "host": "127.0.0.1",          # default serve host
#   "port": 8000,                 # default serve port
#   "package_manager": "uv",      # preferred package manager
#   "architecture": "feature",    # project scaffold pattern
#   "database": "sqlite",         # database driver
#   "python": "python3.12",       # python executable path
#   "auth": "keycloak"            # auth provider
# }


def _read_config() -> dict:
    """Read the .fastman config file."""
    if FASTMAN_CONFIG.exists():
        try:
            return json.loads(FASTMAN_CONFIG.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError):
            return {}
    return {}


def _write_config(config: dict):
    """Write the .fastman config file."""
    FASTMAN_CONFIG.write_text(
        json.dumps(config, indent=2) + "\n", encoding="utf-8"
    )


def _read_locked_env() -> str | None:
    """Read the persisted environment from .fastman config."""
    return _read_config().get("env")


def _write_locked_env(env: str):
    """Persist the selected environment to .fastman config."""
    config = _read_config()
    config["env"] = env
    _write_config(config)


def _resolve_env_file(env: str | None = None) -> Path | None:
    """
    Resolve the env file.
    Priority: explicit env arg > .fastman config > .env.production > .env
    """
    if env:
        env_file = Path(f".env.{env}")
        return env_file if env_file.exists() else None

    # Check persisted selection
    locked = _read_locked_env()
    if locked:
        env_file = Path(f".env.{locked}")
        if env_file.exists():
            return env_file

    # Default auto-detect
    if Path(".env.production").exists():
        return Path(".env.production")
    if Path(".env").exists():
        return Path(".env")
    return None


def _parse_env_file(env_file: Path) -> list[tuple[str, str]]:
    """Parse key=value pairs from an env file, skipping comments and blanks."""
    pairs = []
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            pairs.append((key.strip(), value.strip()))
    return pairs


@register
class ServeCommand(Command):
    signature = "serve {--host=127.0.0.1} {--port=8000} {--reload} {--no-reload} {--env=}"
    description = "Start development server"
    help = """
Examples:
  fastman serve
  fastman serve --port=8080
  fastman serve --host=0.0.0.0 --no-reload
  fastman serve --env=development
  fastman serve --env=staging
"""

    def handle(self):
        host = self.option("host", "127.0.0.1")
        port = self.option("port", "8000")
        env = self.option("env")

        if self.flag("no-reload"):
            reload = False
        elif self.flag("reload"):
            reload = True
        else:
            reload = True

        cmd = PackageManager.get_run_prefix() + [
            "python",
            "-m",
            "uvicorn",
            "app.main:app",
            "--host", host,
            "--port", port
        ]

        if reload:
            cmd.append("--reload")

        # Resolve env file
        # Priority: --env flag > .fastman config > .env.production > .env
        if env:
            env_file = Path(f".env.{env}")
            if not env_file.exists():
                Output.error(f"Environment file not found: {env_file}")
                Output.info("Available env files:")
                for f in sorted(Path(".").glob(".env*")):
                    if f.is_file():
                        Output.echo(f"  {f.name}", Style.GREEN)
                return
        else:
            env_file = _resolve_env_file()

        if env_file:
            cmd.extend(["--env-file", str(env_file)])
            Output.info(f"Using environment: {env_file.name}")

        Output.info(f"Starting server at http://{host}:{port}")
        Output.info("Press CTRL+C to stop")

        try:
            subprocess.run(cmd)
        except KeyboardInterrupt:
            Output.info("\nShutting down server...")


@register
class EnvCommand(Command):
    signature = "env {--source=} {--reset}"
    description = "Set or show the active environment for fastman serve"
    help = """
Set the active environment source. Once set, 'fastman serve' will
automatically use that env file without needing --env.

Examples:
  fastman env                        Show active environment
  fastman env --source=development   Switch to .env.development
  fastman env --source=staging       Switch to .env.staging
  fastman env --source=production    Switch to .env.production
  fastman env --reset                Clear selection, return to auto-detect
"""

    def handle(self):
        env = self.option("source")

        # Handle --reset
        if self.flag("reset"):
            config = _read_config()
            if "env" in config:
                del config["env"]
                _write_config(config)
                Output.success("Environment selection cleared. 'fastman serve' will auto-detect.")
            else:
                Output.info("No environment selection to clear.")
            return

        # If --source provided, persist it
        if env:
            env_file = Path(f".env.{env}")
            if not env_file.exists():
                Output.error(f"Environment file not found: .env.{env}")
                Output.info("Available env files:")
                for f in sorted(Path(".").glob(".env*")):
                    if f.is_file():
                        Output.echo(f"  {f.name}", Style.GREEN)
                return
            _write_locked_env(env)
            Output.success(f"Environment set to: .env.{env}")
            Output.info("'fastman serve' will now use this environment automatically.")
            Output.echo("")

        # List all available env files
        env_files = sorted(f for f in Path(".").glob(".env*") if f.is_file() and f.name != ".fastman")

        if not env_files:
            Output.warn("No .env files found in the current directory.")
            return

        Output.info("Available environment files:")
        resolved = _resolve_env_file()
        locked = _read_locked_env()
        for f in env_files:
            is_active = resolved and f.resolve() == resolved.resolve()
            if is_active and locked:
                marker = "  ← active (locked)"
            elif is_active:
                marker = "  ← active (auto-detected)"
            else:
                marker = ""
            Output.echo(f"  {f.name}{marker}", Style.GREEN if is_active else Style.DIM)

        if not resolved:
            Output.echo("")
            Output.warn("No environment file would be loaded by 'fastman serve'.")
            return

        Output.echo("")
        Output.success(f"Active environment: {resolved.name}")
        Output.echo("")

        pairs = _parse_env_file(resolved)
        if not pairs:
            Output.warn(f"{resolved.name} is empty (no variables defined).")
            return

        # Mask sensitive values
        sensitive = {"password", "secret", "key", "token", "dsn", "database_url", "db_url"}
        rows = []
        for key, value in pairs:
            if any(s in key.lower() for s in sensitive):
                masked = value[:3] + "***" if len(value) > 3 else "***"
                rows.append([key, masked])
            else:
                rows.append([key, value])

        Output.table(["Variable", "Value"], rows, f"Variables from {resolved.name}")

        # Show certificate paths
        Output.echo("")
        certs_dir = Path("certs")
        if certs_dir.is_dir():
            cert_files = sorted(
                p for p in certs_dir.iterdir()
                if p.is_file() and p.suffix in (".pem", ".crt")
            )
            if cert_files:
                Output.info(f"Certificates directory: {certs_dir.resolve()}")
                for f in cert_files:
                    Output.echo(f"  {f.name} → {f.resolve()}", Style.GREEN)
            else:
                Output.info(f"Certificates directory: {certs_dir.resolve()} (empty)")
        else:
            Output.info("Certificates directory: not found (certs/ does not exist)")

        try:
            import certifi
            Output.info(f"Certifi CA bundle: {certifi.where()}")
        except ImportError:
            Output.info("Certifi: not installed")
