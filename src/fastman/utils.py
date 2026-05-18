"""
Utilities and helpers.
"""
import builtins
import keyword
import logging
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from .console import Output

logger = logging.getLogger('fastman')

class NameValidator:
    """Validates and sanitizes names"""

    @staticmethod
    def validate_identifier(name: str) -> str:
        """Validate Python identifier"""
        if not name:
            raise ValueError("Name cannot be empty")

        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', name):
            raise ValueError(
                f"Invalid name '{name}'. Must start with letter and contain only letters, numbers, underscores"
            )

        NameValidator._reject_keyword_or_builtin(name)
        return name

    @staticmethod
    def validate_path_component(name: str) -> str:
        """Validate path component (no traversal)"""
        if not name:
            raise ValueError("Name cannot be empty")

        if '..' in name or '/' in name or '\\' in name:
            raise ValueError(f"Invalid name '{name}'. Cannot contain path separators")

        if name.startswith('-'):
            raise ValueError(f"Invalid name '{name}'. Cannot start with a hyphen.")

        NameValidator._reject_keyword_or_builtin(name.replace('-', '_'))
        return name

    @staticmethod
    def _reject_keyword_or_builtin(name: str) -> None:
        """Raise if `name` collides with a Python keyword, soft keyword, or builtin.

        Generated code would `import` or define this identifier; collision breaks
        either at parse time (hard keywords like ``class``) or causes confusing
        shadowing (``list``, ``type``).
        """
        if keyword.iskeyword(name) or keyword.issoftkeyword(name):
            raise ValueError(
                f"Invalid name '{name}'. It is a Python reserved word."
            )
        if name in dir(builtins):
            raise ValueError(
                f"Invalid name '{name}'. It shadows a Python builtin."
            )

    @staticmethod
    def to_snake_case(name: str) -> str:
        """Convert to snake_case"""
        # Normalize hyphens to underscores
        name = name.replace('-', '_')
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name)
        # Collapse multiple underscores and strip
        return re.sub(r'_+', '_', name).lower().strip('_')

    @staticmethod
    def to_pascal_case(name: str) -> str:
        """Convert to PascalCase"""
        parts = NameValidator.to_snake_case(name).split('_')
        return ''.join(word.capitalize() for word in parts if word)

    @staticmethod
    def to_kebab_case(name: str) -> str:
        """Convert to kebab-case"""
        return NameValidator.to_snake_case(name).replace('_', '-')

    # Common English nouns whose plural form is irregular and not covered by
    # simple suffix rules. Kept short on purpose — anything outside this list
    # falls through to the suffix logic.
    _IRREGULAR_PLURALS = {
        "person": "people",
        "man": "men",
        "woman": "women",
        "child": "children",
        "tooth": "teeth",
        "foot": "feet",
        "mouse": "mice",
        "goose": "geese",
        "ox": "oxen",
        # Latin/Greek -is → -es (common in DB table names)
        "analysis": "analyses",
        "basis": "bases",
        "crisis": "crises",
        "diagnosis": "diagnoses",
        "thesis": "theses",
        "hypothesis": "hypotheses",
        # Words identical in singular & plural (incl. mass nouns)
        "sheep": "sheep",
        "fish": "fish",
        "deer": "deer",
        "series": "series",
        "species": "species",
        "data": "data",
        "info": "info",
        "equipment": "equipment",
    }

    @staticmethod
    def pluralize(name: str) -> str:
        """Return an English plural of `name`.

        Handles irregulars from `_IRREGULAR_PLURALS` and the common suffix
        rules: words ending in s/x/z/ch/sh take `-es`, consonant+y becomes
        `-ies`, vowel+y just adds `-s`. Preserves the original case style by
        operating on a lowered copy and only adjusting the trailing suffix.
        """
        if not name:
            return name

        lowered = name.lower()
        if lowered in NameValidator._IRREGULAR_PLURALS:
            return NameValidator._IRREGULAR_PLURALS[lowered]

        # consonant + y → -ies (party → parties; but day → days)
        if len(lowered) >= 2 and lowered.endswith("y") and lowered[-2] not in "aeiou":
            return name[:-1] + "ies"

        # sibilant endings → -es (bus → buses, box → boxes, dish → dishes, batch → batches)
        if lowered.endswith(("s", "x", "z", "ch", "sh")):
            return name + "es"

        # Default
        return name + "s"


class PathManager:
    """Manages file system operations safely"""

    @staticmethod
    def ensure_dir(path: Path) -> Path:
        """Create directory and __init__.py if needed"""
        path.mkdir(parents=True, exist_ok=True)

        init_file = path / "__init__.py"
        if not init_file.exists():
            init_file.touch()

        return path

    @staticmethod
    def write_file(path: Path, content: str, overwrite: bool = False) -> bool:
        """Write file with safety checks"""
        try:
            # Ensure parent directories exist
            path.parent.mkdir(parents=True, exist_ok=True)

            mode = 'x' if not overwrite else 'w'
            with path.open(mode, encoding='utf-8') as f:
                f.write(content)
            return True
        except FileExistsError:
            Output.warn(f"File already exists: {path}")
            return False
        except PermissionError as e:
            Output.error(f"Permission denied writing to {path}: {e}")
            logger.exception(e)
            return False
        except IsADirectoryError as e:
            Output.error(f"Cannot write file {path}: it is a directory")
            logger.exception(e)
            return False
        except IOError as e:
            Output.error(f"File I/O error writing to {path}: {e}")
            logger.exception(e)
            return False
        except Exception as e:
            Output.error(f"An unexpected error occurred while writing to {path}: {e}")
            logger.exception(e)
            return False

    @staticmethod
    def safe_remove(path: Path) -> bool:
        """Safely remove file or directory"""
        try:
            if not path.exists():
                Output.warn(f"Path does not exist: {path}")
                return False
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path)
            else:
                Output.warn(f"Unknown file type: {path}")
                return False
            return True
        except PermissionError as e:
            Output.error(f"Permission denied removing {path}: {e}")
            return False
        except OSError as e:
            Output.error(f"OS error while removing {path}: {e}")
            return False
        except Exception as e:
            Output.error(f"An unexpected error occurred while removing {path}: {e}")
            return False


class PackageManager:
    """Handles package management across different tools.

    For uv / poetry / pipenv backends the underlying tool finds the project's
    virtualenv on its own. For the **pip** backend, ``sys.executable`` points
    at whatever Python is running fastman (often the *global* interpreter when
    the CLI is installed system-wide), so we explicitly resolve the project's
    ``.venv`` / ``venv`` / ``env`` directory and use *its* pip. That way
    ``fastman install:auth`` and ``fastman package:install`` write to the
    project's venv even if the user forgot to activate it.
    """

    # Directories scanned in order for an existing virtual environment.
    _VENV_CANDIDATES = (".venv", "venv", "env")

    @staticmethod
    def _project_venv_pip() -> Optional[List[str]]:
        """Return the pip executable inside the project's venv, or None.

        Looks for the first venv among `.venv` / `venv` / `env` in the current
        working directory and returns the absolute path to its pip binary.
        """
        cwd = Path.cwd()
        for name in PackageManager._VENV_CANDIDATES:
            venv = cwd / name
            if not venv.is_dir():
                continue
            pip_path = (
                venv / "Scripts" / "pip.exe"
                if os.name == "nt"
                else venv / "bin" / "pip"
            )
            if pip_path.exists():
                return [str(pip_path.resolve())]
        return None

    @staticmethod
    def _pip_command() -> List[str]:
        """Resolve the right pip invocation.

        Order:
          1. Project's venv pip if it exists (best — installs into the project
             even when the user hasn't activated the venv).
          2. ``python -m pip`` using the current interpreter (last resort —
             may install into the global env if fastman runs globally).
        """
        venv_pip = PackageManager._project_venv_pip()
        if venv_pip:
            return venv_pip
        return [sys.executable, "-m", "pip"]

    @staticmethod
    def detect() -> tuple[str, List[str]]:
        """Detect package manager and return (name, run_prefix)"""
        cwd = Path.cwd()

        # Priority: uv.lock > poetry.lock > Pipfile > uv (only if not others) > pip

        if (cwd / "uv.lock").exists():
             return ("uv", ["uv", "run"])

        if (cwd / "poetry.lock").exists():
            return ("poetry", ["poetry", "run"])

        if (cwd / "Pipfile").exists():
            return ("pipenv", ["pipenv", "run"])

        # Look for legacy pip projects
        if (cwd / "requirements.txt").exists() and not (cwd / "pyproject.toml").exists():
            return ("pip", [])

        # Default to uv if it's installed on the system
        if shutil.which("uv"):
            return ("uv", ["uv", "run"])

        return ("pip", [])

    @staticmethod
    def install(packages: List[str], timeout: int = 300) -> bool:
        """Install packages using detected package manager"""
        if not packages:
            return True

        manager, _ = PackageManager.detect()

        try:
            if manager == "uv":
                subprocess.run(["uv", "add"] + packages, check=True, timeout=timeout)
            elif manager == "poetry":
                subprocess.run(["poetry", "add"] + packages, check=True, timeout=timeout)
            elif manager == "pipenv":
                subprocess.run(["pipenv", "install"] + packages, check=True, timeout=timeout)
            else:
                pip_cmd = PackageManager._pip_command()
                if pip_cmd[0] == sys.executable:
                    Output.warn(
                        "No project venv found (.venv/venv/env). Installing with the current "
                        "Python interpreter — this may write to a global site-packages. "
                        "Create a venv first or activate one to scope the install to your project."
                    )
                subprocess.run(pip_cmd + ["install"] + packages, check=True, timeout=timeout)

                # Update requirements.txt
                req_file = Path("requirements.txt")

                existing_bases = set()
                existing_content = ""

                if req_file.exists():
                    existing_content = req_file.read_text()
                    for line in existing_content.splitlines():
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        base_name = re.split(r'[=<>\[]', line)[0].strip().lower()
                        existing_bases.add(base_name)

                with req_file.open("a") as f:
                    for pkg in packages:
                        pkg_base = re.split(r'[=<>\[]', pkg)[0].strip().lower()

                        if pkg_base not in existing_bases:
                            # Ensure the file ends with a newline before appending
                            if existing_content and not existing_content.endswith("\n"):
                                f.write("\n")
                                existing_content += "\n"
                            f.write(f"{pkg}\n")
                            existing_bases.add(pkg_base)
                            existing_content += pkg + "\n"

            return True
        except subprocess.CalledProcessError as e:
            Output.error(f"Package installation failed: {e}")
            return False

    @staticmethod
    def get_run_prefix() -> List[str]:
        """Get command prefix for running scripts"""
        _, prefix = PackageManager.detect()
        return prefix

    @staticmethod
    def remove(packages: List[str], timeout: int = 300) -> bool:
        """Remove packages using detected package manager"""
        if not packages:
            return True

        manager, _ = PackageManager.detect()

        try:
            if manager == "uv":
                subprocess.run(["uv", "remove"] + packages, check=True, timeout=timeout)
            elif manager == "poetry":
                subprocess.run(["poetry", "remove"] + packages, check=True, timeout=timeout)
            elif manager == "pipenv":
                subprocess.run(["pipenv", "uninstall"] + packages, check=True, timeout=timeout)
            else:
                pip_cmd = PackageManager._pip_command()
                subprocess.run(
                    pip_cmd + ["uninstall", "-y"] + packages,
                    check=True,
                    timeout=timeout,
                )

                # Update requirements.txt
                req_file = Path("requirements.txt")
                if req_file.exists():
                    existing_lines = req_file.read_text().splitlines()
                    new_lines = []

                    for line in existing_lines:
                        line_stripped = line.strip()
                        if not line_stripped or line_stripped.startswith("#"):
                            new_lines.append(line)
                            continue

                        # Parse base name
                        base_name = re.split(r'[=<>,[]', line_stripped)[0].strip().lower()
                        # Check if this line should be removed
                        should_remove = False
                        for pkg in packages:
                            pkg_base = re.split(r'[=<>,[]', pkg)[0].strip().lower()
                            if base_name == pkg_base:
                                should_remove = True
                                break

                        if not should_remove:
                            new_lines.append(line)

                    req_file.write_text('\n'.join(new_lines))

            return True
        except subprocess.CalledProcessError as e:
            Output.error(f"Package removal failed: {e}")
            return False


class FastmanConfig:
    """Read access to the per-project `.fastmanrc` file.

    Written by `fastman create` and records `pattern`, `package_manager`,
    and `database`. Other commands use this to detect pattern mismatches (e.g.
    running `make:controller` in a feature-pattern project) without re-deriving
    project shape from the filesystem.
    """

    PATH = Path(".fastmanrc")

    @staticmethod
    def read(cwd: Optional[Path] = None) -> dict:
        """Return the parsed config, or {} if missing/malformed."""
        import json
        path = (cwd or Path.cwd()) / FastmanConfig.PATH
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, OSError, json.JSONDecodeError, ValueError):
            return {}

    @staticmethod
    def pattern(cwd: Optional[Path] = None) -> Optional[str]:
        """Return the project pattern, or None if unrecorded."""
        return FastmanConfig.read(cwd).get("pattern")


class EnvManager:
    """Manages environment files across all environments (dev/staging/prod)"""

    ENV_FILES = [".env", ".env.develop", ".env.staging"]

    @staticmethod
    def append_to_all(block: str, check_key: str, cwd: Path = None):
        """Append a block of env vars to all env files if check_key is not already present"""
        base = cwd or Path.cwd()
        for env_file in EnvManager.ENV_FILES:
            env_path = base / env_file
            if env_path.exists():
                content = env_path.read_text(encoding='utf-8')
                if check_key not in content:
                    content += block
                    env_path.write_text(content, encoding='utf-8')

    @staticmethod
    def append_to_env(env_path: Path, block: str, check_key: str):
        """Append a block to a single env file if check_key is not already present"""
        if env_path.exists():
            content = env_path.read_text(encoding='utf-8')
            if check_key not in content:
                content += block
                env_path.write_text(content, encoding='utf-8')
