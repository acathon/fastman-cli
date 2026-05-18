"""
Drift detection + re-scaffold logic for ``fastman update``.

Concept
-------

A project created by ``fastman create`` (or extended via ``install:auth``
/ ``install:mail``) contains files whose contents are owned by the
generator — ``app/core/database.py``, ``alembic/env.py``,
``app/core/mail.py``, etc. As fastman ships new versions, those
templates evolve: v0.3.x emitted ``declarative_base()``; v0.4.x emits
``DeclarativeBase``. The user has no way to pull in those improvements
without recreating their project from scratch.

``fastman update`` closes that gap. For every file fastman knows about,
it renders the *current* template (using the project's recorded
``.fastmanrc`` for pattern/database/etc.), compares it to what's on
disk, and lets the user decide per file: keep theirs, take fastman's,
or skip.

What this module owns
---------------------

- A catalog of (template_name, destination_path) pairs per project shape.
  Detection of which integrations are installed (mail, auth, ...) is
  filesystem-based — same heuristics as ``fastman about``.
- The :class:`Drift` dataclass + :func:`compute_drifts` for diffing.
- :func:`apply_drift` to actually write the new contents.

What this module does NOT do
----------------------------

- It does not touch files fastman did not originate (the user's own
  features, routes, models — those are theirs).
- It does not perform a three-way merge. The choice is binary per file:
  keep yours or take fastman's. Hand-merges are on the user.
- It does not roll back. Backups are the user's job (commit before
  running ``update``).
"""
from __future__ import annotations

import difflib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .templates import Template, TemplateLoader, Templates
from .utils import FastmanConfig


# ── File catalog ───────────────────────────────────────────────────────


@dataclass(frozen=True)
class Recipe:
    """Describes one file fastman owns.

    Attributes
    ----------
    dest: project-relative destination path (e.g. ``"app/core/database.py"``).
    renderer: callable that takes a context dict and returns the file's
        current desired contents. We use callables (not template names)
        because some files need extra rendering steps (e.g. CONFIG renders
        ``config_db_fields`` as a sub-template first).
    """

    dest: str
    renderer: callable

    def render(self, ctx: dict) -> str:
        return self.renderer(ctx)


def _render_main_app(ctx: dict) -> str:
    return Template.render(Templates.MAIN_APP, ctx)


def _render_config(ctx: dict) -> str:
    """Render CONFIG, including the nested config_db_fields sub-template."""
    inner_ctx = dict(ctx)
    inner_ctx["config_db_fields"] = Template.render(
        _CONFIG_DB_FIELDS[ctx["database"]], ctx
    )
    return Template.render(Templates.CONFIG, inner_ctx)


def _render_database(ctx: dict) -> str:
    table = {
        "sqlite": Templates.DATABASE,
        "postgresql": Templates.DATABASE_POSTGRESQL,
        "mysql": Templates.DATABASE_MYSQL,
        "oracle": Templates.DATABASE_ORACLE,
        "firebase": Templates.DATABASE_FIREBASE,
    }
    return Template.render(table.get(ctx["database"], Templates.DATABASE), ctx)


def _render_logging(ctx: dict) -> str:
    return Template.render(Templates.LOGGING, ctx)


def _render_discovery(ctx: dict) -> str:
    return Template.render(Templates.DISCOVERY, ctx)


def _render_graphql(ctx: dict) -> str:
    return Template.render(Templates.GRAPHQL, ctx)


def _render_alembic_env(ctx: dict) -> str:
    return Template.render(Templates.ALEMBIC_ENV, ctx)


def _render_alembic_ini(ctx: dict) -> str:
    return Template.render(Templates.ALEMBIC_INI, ctx)


def _render_alembic_script_mako(ctx: dict) -> str:
    return Template.render(Templates.ALEMBIC_SCRIPT_MAKO, ctx)


def _render_gitignore(ctx: dict) -> str:
    return Template.render(Templates.GITIGNORE, ctx)


def _render_mail_loader(template_name: str):
    """Build a renderer that loads a mail .j2 file by name."""
    def render(ctx: dict) -> str:
        return TemplateLoader.render(template_name, ctx)
    return render


# config_db_fields is exposed by NewCommand._get_config_db_fields; we
# duplicate the dict here so update doesn't have to import the command.
# Keep in sync with src/fastman/commands/project.py.
_CONFIG_DB_FIELDS = {
    "sqlite": '''# Database
    DATABASE_URL: Optional[str] = "sqlite:///./app.db"
''',
    "postgresql": '''# Database (PostgreSQL)
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""
    DB_NAME: str = "{{ project_name }}"
    DATABASE_URL: Optional[str] = None

    @computed_field
    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
''',
    "mysql": '''# Database (MySQL)
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "{{ project_name }}"
    DATABASE_URL: Optional[str] = None

    @computed_field
    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
''',
    "oracle": '''# Database (Oracle)
    DB_HOST: str = "localhost"
    DB_PORT: int = 1521
    DB_USER: str = "system"
    DB_PASSWORD: str = ""
    DB_NAME: str = "XE"
    DATABASE_URL: Optional[str] = None

    @computed_field
    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"oracle+oracledb://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
''',
    "firebase": '''# Firebase (NoSQL)
    FIREBASE_PROJECT_ID: Optional[str] = None
    FIREBASE_CREDENTIALS_PATH: Optional[str] = None
''',
}


def core_recipes(database: str) -> list[Recipe]:
    """Files generated for every project regardless of pattern."""
    recipes = [
        Recipe("app/main.py", _render_main_app),
        Recipe("app/core/config.py", _render_config),
        Recipe("app/core/logging.py", _render_logging),
        Recipe("app/core/discovery.py", _render_discovery),
        Recipe(".gitignore", _render_gitignore),
    ]
    # Database module — firebase has its own filename.
    if database == "firebase":
        recipes.append(Recipe("app/core/firebase.py", _render_database))
    else:
        recipes.append(Recipe("app/core/database.py", _render_database))
        # Alembic files only for SQL databases.
        recipes.append(Recipe("alembic/env.py", _render_alembic_env))
        recipes.append(Recipe("alembic.ini", _render_alembic_ini))
        recipes.append(Recipe("alembic/script.py.mako", _render_alembic_script_mako))
    return recipes


def mail_recipes() -> list[Recipe]:
    """Files generated when install:mail has been run."""
    return [
        Recipe("app/core/mail.py", _render_mail_loader("mail/core_mail.py.j2")),
        Recipe("app/mail/__init__.py", _render_mail_loader("mail/__init__.py.j2")),
        Recipe("app/mail/base.py", _render_mail_loader("mail/base.py.j2")),
    ]


# Auth files vary per type; renderers below dispatch on `auth_type`.
def _auth_recipes(auth_type: str) -> list[Recipe]:
    if auth_type == "keycloak":
        return [
            Recipe(
                "app/core/keycloak.py",
                _render_mail_loader("auth/keycloak/keycloak.py.j2"),
            ),
        ]
    if auth_type == "jwt":
        return [
            Recipe("app/features/auth/security.py", _render_mail_loader("auth/jwt/security.py.j2")),
            Recipe("app/features/auth/models.py", _render_mail_loader("auth/jwt/models.py.j2")),
            Recipe("app/features/auth/schemas.py", _render_mail_loader("auth/jwt/schemas.py.j2")),
            Recipe("app/features/auth/service.py", _render_mail_loader("auth/jwt/service.py.j2")),
            Recipe("app/features/auth/dependencies.py", _render_mail_loader("auth/jwt/dependencies.py.j2")),
            Recipe("app/features/auth/router.py", _render_mail_loader("auth/jwt/router.py.j2")),
        ]
    if auth_type == "passkey":
        return [
            Recipe("app/features/auth/models.py", _render_mail_loader("auth/passkey/models.py.j2")),
            Recipe("app/features/auth/schemas.py", _render_mail_loader("auth/passkey/schemas.py.j2")),
            Recipe("app/features/auth/service.py", _render_mail_loader("auth/passkey/service.py.j2")),
            Recipe("app/features/auth/security.py", _render_mail_loader("auth/passkey/security.py.j2")),
            Recipe("app/features/auth/dependencies.py", _render_mail_loader("auth/passkey/dependencies.py.j2")),
            Recipe("app/features/auth/router.py", _render_mail_loader("auth/passkey/router.py.j2")),
        ]
    # OAuth needs a provider — caller passes it in via context. Skip
    # from auto-detection for now; user can re-run install:auth.
    return []


def _detect_auth_type(cwd: Path) -> Optional[str]:
    """Filesystem-based auth detection. Mirrors AboutCommand."""
    if (cwd / "app/core/keycloak.py").is_file():
        return "keycloak"
    auth = cwd / "app/features/auth"
    if not auth.is_dir():
        return None
    if (auth / "security.py").is_file() and (auth / "service.py").is_file():
        # JWT and Passkey both have security.py; passkey has webauthn imports.
        sec = (auth / "security.py").read_text(encoding="utf-8")
        if "webauthn" in sec or "ACCESS_TOKEN_EXPIRE_MINUTES = 60" in sec:
            return "passkey"
        return "jwt"
    if (auth / "oauth_config.py").is_file():
        return "oauth"
    return None


def _has_mail(cwd: Path) -> bool:
    return (cwd / "app/core/mail.py").is_file()


# ── Drift detection ────────────────────────────────────────────────────


@dataclass
class Drift:
    """A single file whose on-disk content differs from what fastman would emit today."""

    path: Path                # absolute path on disk
    relative: str             # human-friendly relative path
    current: str              # what's on disk now
    desired: str              # what fastman would generate today
    missing: bool = False     # True if the file doesn't exist on disk

    @property
    def diff(self) -> str:
        """Unified diff string suitable for printing."""
        if self.missing:
            return f"(file is missing — would be created from template)\n{self.desired}"
        return "".join(
            difflib.unified_diff(
                self.current.splitlines(keepends=True),
                self.desired.splitlines(keepends=True),
                fromfile=f"{self.relative} (your version)",
                tofile=f"{self.relative} (fastman target)",
                n=3,
            )
        )


def compute_drifts(
    cwd: Path,
    *,
    include_auth: bool = True,
    include_mail: bool = True,
) -> list[Drift]:
    """Compute every drifted fastman-owned file in `cwd`.

    Returns drifts in catalog order — caller decides how to present them
    (interactive prompts, batch apply, --check exit code, etc.).
    """
    config = FastmanConfig.read(cwd)
    if not config:
        # No .fastmanrc — fall back to filesystem inference. Not 100%
        # accurate but lets pre-0.4.0 projects use `fastman update`.
        config = _infer_config_from_filesystem(cwd)

    if not config.get("database"):
        # Can't render without knowing the database driver.
        return []

    ctx = {
        "project_name": cwd.name,
        "version": _fastman_version(),
        "secret_key": "<see-your-.env>",
        "database": config["database"],
    }

    recipes: list[Recipe] = []
    recipes.extend(core_recipes(config["database"]))

    if include_mail and _has_mail(cwd):
        recipes.extend(mail_recipes())

    if include_auth:
        auth_type = _detect_auth_type(cwd)
        if auth_type and auth_type != "oauth":
            recipes.extend(_auth_recipes(auth_type))

    drifts: list[Drift] = []
    for recipe in recipes:
        abs_path = cwd / recipe.dest
        try:
            desired = recipe.render(ctx)
        except Exception:
            # A renderer that needs context we don't have here (e.g. an
            # OAuth provider name) — silently skip rather than crashing
            # the whole update.
            continue

        if not abs_path.exists():
            drifts.append(Drift(
                path=abs_path,
                relative=recipe.dest,
                current="",
                desired=desired,
                missing=True,
            ))
            continue

        current = abs_path.read_text(encoding="utf-8")
        if current != desired:
            drifts.append(Drift(
                path=abs_path,
                relative=recipe.dest,
                current=current,
                desired=desired,
            ))

    return drifts


def apply_drift(drift: Drift) -> None:
    """Overwrite the on-disk file with the fastman-generated version.

    Creates parent directories if needed. Used by ``fastman update`` after
    the user accepts the change for a given file.
    """
    drift.path.parent.mkdir(parents=True, exist_ok=True)
    drift.path.write_text(drift.desired, encoding="utf-8")


# ── Internals ──────────────────────────────────────────────────────────


def _fastman_version() -> str:
    from . import __version__
    return __version__


def _infer_config_from_filesystem(cwd: Path) -> dict:
    """Best-effort recovery when .fastmanrc is missing (pre-0.4.0 projects)."""
    config: dict = {}
    # Database
    if (cwd / "app/core/firebase.py").is_file():
        config["database"] = "firebase"
    else:
        db_file = cwd / "app/core/database.py"
        if db_file.is_file():
            content = db_file.read_text(encoding="utf-8")
            for driver, marker in (
                ("postgresql", "postgresql"),
                ("mysql", "pymysql"),
                ("oracle", "oracledb"),
                ("sqlite", "sqlite"),
            ):
                if marker in content.lower():
                    config["database"] = driver
                    break
    # Pattern
    if (cwd / "app/features").is_dir():
        config["pattern"] = "feature"
    elif (cwd / "app/controllers").is_dir():
        config["pattern"] = "layer"
    elif (cwd / "app/api").is_dir():
        config["pattern"] = "api"
    return config
