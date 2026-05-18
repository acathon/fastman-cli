"""
Database and migration commands.
"""
import importlib
import logging
import re
import subprocess
import sys
from pathlib import Path

from ..console import Output, Style
from ..utils import NameValidator, PackageManager
from .base import Command, register

logger = logging.getLogger("fastman")


def _require_alembic() -> bool:
    """Refuse to run alembic-backed commands when alembic isn't configured.

    Firebase projects and any project where the user ran `fastman init` (which
    doesn't scaffold alembic) will hit this. Returning False prints an
    actionable hint instead of a cryptic alembic stack trace.
    """
    if Path("alembic.ini").exists():
        return True
    Output.error("alembic.ini not found in the current directory.")
    Output.info("This project doesn't use Alembic migrations.")
    Output.info(
        "Alembic is scaffolded for SQL projects (sqlite/postgres/mysql/oracle). "
        "Firebase projects don't use it."
    )
    return False


@register
class MakeMigrationCommand(Command):
    signature = "make:migration {message}"
    description = "Create database migration"
    help = """
Examples:
  fastman make:migration "create users table"
  fastman make:migration "add email_verified column"

Wraps `alembic revision --autogenerate`. Spaces in the message are
converted to underscores and non-word characters stripped.
"""

    def handle(self):
        if not _require_alembic():
            return

        message = self.argument(0, "update")

        # Sanitize message for use in filenames and commands
        sanitized_message = re.sub(r'\s+', '_', message)
        sanitized_message = re.sub(r'[^\w-]', '', sanitized_message).strip('_')

        if not sanitized_message:
            sanitized_message = "update"

        cmd = PackageManager.get_run_prefix() + [
            "python", "-m", "alembic", "revision", "--autogenerate", "-m", sanitized_message
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                Output.success(f"Migration created: {sanitized_message}")
                if result.stdout.strip():
                    # Surface alembic's "Detected added column..." chatter so
                    # the user can spot empty/wrong migrations early.
                    Output.info("Alembic output:")
                    Output.echo(result.stdout.strip(), Style.DIM)
                Output.info("Review the migration file before running database:migrate")
            else:
                Output.error("Migration failed:")
                if result.stderr.strip():
                    Output.echo(result.stderr.strip(), Style.RED)
        except FileNotFoundError:
            Output.error("alembic command not found. Is it installed in your venv?")
        except Exception as e:
            Output.error(f"Failed to create migration: {e}")


@register
class DatabaseMigrateCommand(Command):
    signature = "database:migrate"
    description = "Run database migrations"
    help = """
Examples:
  fastman database:migrate

Runs `alembic upgrade head`. Refuses to run when alembic.ini is missing
(Firebase projects don't scaffold Alembic).
"""

    def handle(self):
        if not _require_alembic():
            return

        cmd = PackageManager.get_run_prefix() + ["python", "-m", "alembic", "upgrade", "head"]

        Output.info("Running migrations...")
        try:
            result = subprocess.run(cmd)
            if result.returncode == 0:
                Output.success("Migrations completed")
            else:
                Output.error("Migration failed")
        except FileNotFoundError:
            Output.error("alembic command not found. Is it installed in your venv?")
        except Exception as e:
            Output.error(f"Failed to run migrations: {e}")


@register
class MigrateRollbackCommand(Command):
    signature = "migrate:rollback {--steps=1}"
    description = "Rollback database migrations"
    help = """
Examples:
  fastman migrate:rollback
  fastman migrate:rollback --steps=3
"""

    def handle(self):
        if not _require_alembic():
            return

        steps = self.option("steps", "1")

        try:
            steps_int = int(steps)
            if steps_int < 1:
                raise ValueError
        except ValueError:
            Output.error("Invalid steps value. Must be a positive integer.")
            return

        if not Output.confirm(f"Rollback {steps_int} migration(s)?", default=False):
            Output.info("Cancelled")
            return

        cmd = PackageManager.get_run_prefix() + ["python", "-m", "alembic", "downgrade", f"-{steps_int}"]

        try:
            result = subprocess.run(cmd)
            if result.returncode == 0:
                Output.success(f"Rolled back {steps_int} migration(s)")
            else:
                Output.error("Rollback failed")
        except FileNotFoundError:
            Output.error("alembic command not found. Is it installed in your venv?")
        except Exception as e:
            Output.error(f"Failed to rollback: {e}")


@register
class MigrateStatusCommand(Command):
    signature = "migrate:status"
    description = "Show migration status"
    help = """
Examples:
  fastman migrate:status

Prints the current Alembic revision. Useful as a "what state am I in"
check before running fastman database:migrate.
"""

    def handle(self):
        if not _require_alembic():
            return

        cmd = PackageManager.get_run_prefix() + ["python", "-m", "alembic", "current"]

        try:
            subprocess.run(cmd)
        except FileNotFoundError:
            Output.error("alembic command not found. Is it installed in your venv?")
        except Exception as e:
            Output.error(f"Failed to get status: {e}")


@register
class DatabaseSeedCommand(Command):
    signature = "database:seed {--class=}"
    description = "Run database seeders"
    help = """
Examples:
  fastman database:seed
  fastman database:seed --class=UserSeeder
"""

    def handle(self):
        seeder_class = self.option("class")

        cwd_path = str(Path.cwd())
        path_added = cwd_path not in sys.path
        if path_added:
            sys.path.insert(0, cwd_path)

        try:
            from app.core.database import SessionLocal

            db = None
            try:
                db = SessionLocal()

                seeders_path = Path("database/seeders")
                if not seeders_path.exists():
                    Output.error("Seeders directory not found")
                    return

                count = 0
                for file_path in seeders_path.glob("*_seeder.py"):
                    module_name = file_path.stem

                    # Match class name or module name
                    # Normalize file stem to PascalCase to match typical class names (e.g. user_seeder -> UserSeeder)
                    expected_class = NameValidator.to_pascal_case(module_name)

                    if seeder_class and seeder_class != module_name and seeder_class != expected_class:
                        continue

                    try:
                        module = importlib.import_module(f"database.seeders.{module_name}")

                        # Find seeder class
                        for attr_name in dir(module):
                            if attr_name.endswith("Seeder") and attr_name != "Seeder":
                                seeder_cls = getattr(module, attr_name)
                                Output.info(f"Running {attr_name}...")
                                seeder_cls.run(db)
                                count += 1

                    except (ImportError, AttributeError) as e:
                        Output.error(f"Failed to load or run seeder {module_name}: {e}")
                        logger.exception(e)
                    except Exception as e:
                        Output.error(f"An unexpected error occurred while running {module_name}: {e}")
                        logger.exception(e)

                if count > 0:
                    Output.success(f"Ran {count} seeder(s)")
                else:
                    Output.warn("No seeders found")

            finally:
                if db:
                    db.close()

        except ImportError as e:
            Output.error(f"Failed to import database session: {e}")
            logger.exception(e)
        except Exception as e:
            Output.error(f"An unexpected error occurred during seeding: {e}")
            logger.exception(e)
        finally:
            if path_added and cwd_path in sys.path:
                sys.path.remove(cwd_path)
