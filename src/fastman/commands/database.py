"""
Database and migration commands.
"""
import re
import subprocess
import sys
import importlib
from pathlib import Path

from .base import Command, register
from ..console import Output, Style
from ..utils import PackageManager, NameValidator
import logging

logger = logging.getLogger("fastman")


@register
class MakeMigrationCommand(Command):
    signature = "make:migration {message}"
    description = "Create database migration"

    def handle(self):
        message = self.argument(0, "update")

        # Sanitize message for use in filenames and commands
        sanitized_message = re.sub(r'\s+', '_', message)
        sanitized_message = re.sub(r'[^\w-]', '', sanitized_message).strip('_')

        if not sanitized_message:
            sanitized_message = "update"

        cmd = PackageManager.get_run_prefix() + [
            "alembic", "revision", "--autogenerate", "-m", sanitized_message
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                Output.success(f"Migration created: {sanitized_message}")
                Output.info("Review the migration file before running migrate")
            else:
                Output.error(f"Migration failed: {result.stderr}")
        except Exception as e:
            Output.error(f"Failed to create migration: {e}")


@register
class DatabaseMigrateCommand(Command):
    signature = "database:migrate"
    description = "Run database migrations"

    def handle(self):
        cmd = PackageManager.get_run_prefix() + ["alembic", "upgrade", "head"]

        Output.info("Running migrations...")
        try:
            result = subprocess.run(cmd)
            if result.returncode == 0:
                Output.success("Migrations completed")
            else:
                Output.error("Migration failed")
        except Exception as e:
            Output.error(f"Failed to run migrations: {e}")


@register
class MigrateRollbackCommand(Command):
    signature = "migrate:rollback {--steps=1}"
    description = "Rollback database migrations"

    def handle(self):
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

        cmd = PackageManager.get_run_prefix() + ["alembic", "downgrade", f"-{steps_int}"]

        try:
            result = subprocess.run(cmd)
            if result.returncode == 0:
                Output.success(f"Rolled back {steps_int} migration(s)")
            else:
                Output.error("Rollback failed")
        except Exception as e:
            Output.error(f"Failed to rollback: {e}")


@register
class MigrateResetCommand(Command):
    signature = "migrate:reset"
    description = "Reset database (rollback all migrations)"

    def handle(self):
        if not Output.confirm("⚠️  Reset ALL migrations? This cannot be undone!", default=False):
            Output.info("Cancelled")
            return

        cmd = PackageManager.get_run_prefix() + ["alembic", "downgrade", "base"]

        try:
            result = subprocess.run(cmd)
            if result.returncode == 0:
                Output.success("Database reset complete")
            else:
                Output.error("Reset failed")
        except Exception as e:
            Output.error(f"Failed to reset: {e}")


@register
class MigrateStatusCommand(Command):
    signature = "migrate:status"
    description = "Show migration status"

    def handle(self):
        cmd = PackageManager.get_run_prefix() + ["alembic", "current"]

        try:
            subprocess.run(cmd)
        except Exception as e:
            Output.error(f"Failed to get status: {e}")


@register
class DatabaseSeedCommand(Command):
    signature = "database:seed {--class=}"
    description = "Run database seeders"

    def handle(self):
        seeder_class = self.option("class")

        cwd_path = str(Path.cwd())
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
            # Clean up sys.path to avoid pollution
            if cwd_path in sys.path:
                sys.path.remove(cwd_path)
