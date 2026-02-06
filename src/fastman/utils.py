"""
Utilities and helpers.
"""
import re
import shutil
import subprocess
import sys
import logging
from pathlib import Path
from typing import List

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

        return name

    @staticmethod
    def validate_path_component(name: str) -> str:
        """Validate path component (no traversal)"""
        if not name:
            raise ValueError("Name cannot be empty")

        if '..' in name or '/' in name or '\\' in name:
            raise ValueError(f"Invalid name '{name}'. Cannot contain path separators")

        return name

    @staticmethod
    def to_snake_case(name: str) -> str:
        """Convert to snake_case"""
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name)
        return name.lower().strip('_')

    @staticmethod
    def to_pascal_case(name: str) -> str:
        """Convert to PascalCase"""
        parts = NameValidator.to_snake_case(name).split('_')
        return ''.join(word.capitalize() for word in parts if word)

    @staticmethod
    def to_kebab_case(name: str) -> str:
        """Convert to kebab-case"""
        return NameValidator.to_snake_case(name).replace('_', '-')


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
            with path.open('x' if not overwrite else 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except FileExistsError:
            Output.warn(f"File already exists: {path}")
            return False

        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            path.write_text(content, encoding='utf-8')
            return True
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
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path)
            return True
        except OSError as e:
            Output.error(f"OS error while removing {path}: {e}")
            return False
        except Exception as e:
            Output.error(f"An unexpected error occurred while removing {path}: {e}")
            return False


class PackageManager:
    """Handles package management across different tools"""

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

        # Check for uv binary and pyproject.toml but ONLY if no other lockfiles exist
        # This prevents false positives where uv is installed but not used for this project
        if (shutil.which("uv") and (cwd / "pyproject.toml").exists()):
            return ("uv", ["uv", "run"])

        return ("pip", [])

    @staticmethod
    def install(packages: List[str]) -> bool:
        """Install packages using detected package manager"""
        if not packages:
            return True

        manager, _ = PackageManager.detect()

        try:
            if manager == "uv":
                subprocess.run(["uv", "add"] + packages, check=True)
            elif manager == "poetry":
                subprocess.run(["poetry", "add"] + packages, check=True)
            elif manager == "pipenv":
                subprocess.run(["pipenv", "install"] + packages, check=True)
            else:
                subprocess.run([sys.executable, "-m", "pip", "install"] + packages, check=True)

                # Update requirements.txt
                req_file = Path("requirements.txt")
                if req_file.exists():
                    existing = req_file.read_text().splitlines()
                    for pkg in packages:
                        if pkg not in existing:
                            with req_file.open("a") as f:
                                f.write(f"\n{pkg}")

            return True
        except subprocess.CalledProcessError as e:
            Output.error(f"Package installation failed: {e}")
            return False

    @staticmethod
    def get_run_prefix() -> List[str]:
        """Get command prefix for running scripts"""
        _, prefix = PackageManager.detect()
        return prefix
