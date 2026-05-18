"""
Database and migration commands.
"""
import importlib
import logging
import os
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
class DatabaseFreshCommand(Command):
    """Wipe + migrate + (optionally) seed in one shot — dev loop convenience."""

    signature = "db:fresh {--seed} {--force}"
    description = "Drop all tables, re-run migrations, optionally re-seed"
    help = """
Examples:
  fastman db:fresh                # confirm, then downgrade base + upgrade head
  fastman db:fresh --seed         # also run database:seed afterwards
  fastman db:fresh --force        # skip the confirmation prompt (CI)
  fastman db:fresh --seed --force

What it does:
  1. alembic downgrade base       (drop every migrated table)
  2. alembic upgrade head         (reapply every migration)
  3. database:seed (if --seed)    (run all seeders)

Destructive — every row in every migrated table is lost. The
confirmation prompt is shown unless --force or --no-interaction is
passed. Production safety net: refuses to run when ENVIRONMENT=production.
"""

    def handle(self):
        if not _require_alembic():
            return

        # Production guard. Even with --force, refuse to wipe a prod DB
        # accidentally. If a user really wants this, they can override
        # ENVIRONMENT explicitly before the call.
        if os.environ.get("ENVIRONMENT") == "production":
            Output.error(
                "Refusing to run db:fresh with ENVIRONMENT=production. "
                "If this is intentional, unset ENVIRONMENT or run the alembic "
                "commands manually."
            )
            return

        force = self.flag("force")
        do_seed = self.flag("seed")

        if not force and not self.no_interaction:
            preview = (
                "This will DROP every migrated table, then recreate them"
                + (" and re-run all seeders." if do_seed else ".")
            )
            Output.warn(preview)
            if not Output.confirm("Continue?", default=False):
                Output.info("Cancelled.")
                return

        prefix = PackageManager.get_run_prefix()

        # Step 1: downgrade to base — drops every alembic-tracked table.
        Output.info("Step 1/3: alembic downgrade base")
        result = subprocess.run(prefix + ["python", "-m", "alembic", "downgrade", "base"])
        if result.returncode != 0:
            Output.error("Downgrade failed. Aborting.")
            return

        # Step 2: upgrade head — reapply every migration.
        Output.info("Step 2/3: alembic upgrade head")
        result = subprocess.run(prefix + ["python", "-m", "alembic", "upgrade", "head"])
        if result.returncode != 0:
            Output.error("Upgrade failed. Database may be in an intermediate state.")
            return

        # Step 3: optional seed.
        if do_seed:
            Output.info("Step 3/3: database:seed")
            # Reuse the existing seeder command rather than duplicating logic.
            DatabaseSeedCommand([], self.context).handle()
        else:
            Output.info("Step 3/3: skipped (pass --seed to also re-seed)")

        Output.success("Database refreshed.")


@register
class ModelShowCommand(Command):
    """SQLAlchemy model introspection — columns, relations, indexes.

    Replaces the v0.4.0-removed `inspect` command for the SA-model case
    (which was its main use). Loads the project's models, finds the named
    class, and renders its table structure as a Rich table.
    """

    signature = "model:show {name}"
    description = "Introspect a SQLAlchemy model — columns, relations, indexes"
    help = """
Examples:
  fastman model:show User
  fastman model:show Order
  fastman model:show order      (snake_case also accepted)

Walks app/models/, app/features/*/models.py, and app/api/*/models.py to
find a class matching `name` (case-insensitive, snake/Pascal-tolerant).
Renders columns with type/nullable/PK markers and lists any relationships.
"""

    def handle(self):
        name = self.prompt_argument(0, "Model name")
        if not name:
            Output.error("Model name is required.")
            return

        cwd_path = str(Path.cwd())
        path_added = cwd_path not in sys.path
        if path_added:
            sys.path.insert(0, cwd_path)

        try:
            model_class = self._locate_model(name)
            if model_class is None:
                Output.error(f"Model '{name}' not found.")
                Output.info(
                    "Searched: app/models/, app/features/*/models.py, "
                    "app/api/*/models.py"
                )
                return
            self._render_model(model_class)
        except ImportError as e:
            Output.error(f"Could not import project models: {e}")
            Output.info("Make sure the project's venv is active or use `uv run fastman model:show`.")
        finally:
            if path_added and cwd_path in sys.path:
                sys.path.remove(cwd_path)

    # ── Discovery ──────────────────────────────────────────────────

    def _locate_model(self, requested: str):
        """Walk the project's model modules and return the first class match.

        Match is case-insensitive and tolerant of snake_case/PascalCase
        (so `model:show user_profile` finds class `UserProfile`).
        """
        targets = {
            requested,
            NameValidator.to_pascal_case(requested),
            NameValidator.to_snake_case(requested),
        }
        targets = {t.lower() for t in targets}

        candidates: list[str] = []
        if Path("app/models").is_dir():
            for f in sorted(Path("app/models").glob("*.py")):
                if f.name != "__init__.py" and not f.name.startswith("_"):
                    candidates.append(f"app.models.{f.stem}")
        for sub in ("features", "api"):
            base = Path("app") / sub
            if base.is_dir():
                for child in sorted(base.iterdir()):
                    if child.is_dir() and (child / "models.py").exists():
                        candidates.append(f"app.{sub}.{child.name}.models")

        for module_path in candidates:
            try:
                module = importlib.import_module(module_path)
            except Exception:
                continue
            for attr_name in dir(module):
                if attr_name.lower() in targets:
                    cls = getattr(module, attr_name)
                    # Filter to actual SA model classes (have __tablename__).
                    if hasattr(cls, "__tablename__"):
                        return cls
        return None

    # ── Rendering ──────────────────────────────────────────────────

    def _render_model(self, cls) -> None:
        """Print a model's structure as a Rich table (or plain fallback)."""
        Output.section(f"Model: {cls.__name__}", f"table: {cls.__tablename__}")

        # Columns table.
        rows = []
        for column in cls.__table__.columns:
            flags = []
            if column.primary_key:
                flags.append("PK")
            if not column.nullable:
                flags.append("NOT NULL")
            if column.unique:
                flags.append("UNIQUE")
            if column.index:
                flags.append("INDEX")
            if column.foreign_keys:
                fks = ", ".join(str(fk.column) for fk in column.foreign_keys)
                flags.append(f"FK -> {fks}")
            default = ""
            if column.default is not None:
                default = repr(getattr(column.default, "arg", column.default))
            elif column.server_default is not None:
                default = "server_default"
            rows.append([
                column.name,
                str(column.type),
                " ".join(flags) or "—",
                default or "—",
            ])
        Output.table(["Column", "Type", "Constraints", "Default"], rows)

        # Relationships.
        try:
            from sqlalchemy import inspect as sa_inspect
            mapper = sa_inspect(cls)
            rels = list(mapper.relationships)
        except Exception:
            rels = []

        if rels:
            Output.new_line()
            rel_rows = [
                [
                    rel.key,
                    rel.mapper.class_.__name__,
                    rel.direction.name.lower(),
                    "yes" if rel.uselist else "no",
                ]
                for rel in rels
            ]
            Output.table(
                ["Relationship", "Target", "Direction", "Collection"],
                rel_rows,
                "Relations",
            )

        # Indexes (declared on the table, not just on individual columns).
        table_indexes = [idx for idx in cls.__table__.indexes]
        if table_indexes:
            Output.new_line()
            idx_rows = [
                [idx.name or "—", ", ".join(c.name for c in idx.columns), "yes" if idx.unique else "no"]
                for idx in table_indexes
            ]
            Output.table(["Index", "Columns", "Unique"], idx_rows, "Indexes")


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
