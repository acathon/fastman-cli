"""
Package install / remove commands.

These are deliberately thin wrappers around :class:`PackageManager`. They earn
their keep by:

1. Picking the right backend automatically (uv / poetry / pipenv / pip) based
   on the project's lock files, so users don't need to remember which tool
   manages each project.
2. For the **pip** backend, routing through the project's own `.venv` pip
   even when the user hasn't activated the venv. The bare `pip install` they
   would otherwise run could land in a global site-packages.

If you're on uv / poetry / pipenv, calling those tools directly (`uv add X`,
`poetry add X`, `pipenv install X`) is equally fine — the underlying tools
already manage the venv.
"""
from ..console import Output
from ..utils import PackageManager
from .base import Command, register


@register
class PackageInstallCommand(Command):
    signature = "package:install {package}"
    description = "Install a Python package into the project's venv"
    help = """
Examples:
  fastman package:install requests
  fastman package:install "sqlalchemy>=2.0"
  fastman package:install fastapi httpx        # (one package per call for now)

Picks the right backend (uv/poetry/pipenv/pip) automatically. On pip, installs
into the project's .venv even when not activated.
"""

    def handle(self):
        package = self.argument(0)
        if not package:
            Output.error("Package name required")
            Output.info("Example: fastman package:install requests")
            return

        Output.info(f"Installing {package}...")
        if PackageManager.install([package]):
            Output.success(f"Package '{package}' installed")
        else:
            Output.error(f"Failed to install '{package}'")


@register
class PackageRemoveCommand(Command):
    signature = "package:remove {package}"
    description = "Remove a Python package from the project's venv"
    help = """
Examples:
  fastman package:remove requests
  fastman package:remove "sqlalchemy"

Picks the right backend (uv/poetry/pipenv/pip) automatically. On pip, also
strips the entry from requirements.txt.
"""

    def handle(self):
        package = self.argument(0)
        if not package:
            Output.error("Package name required")
            Output.info("Example: fastman package:remove requests")
            return

        Output.info(f"Removing {package}...")
        if PackageManager.remove([package]):
            Output.success(f"Package '{package}' removed")
        else:
            Output.error(f"Failed to remove '{package}'")
