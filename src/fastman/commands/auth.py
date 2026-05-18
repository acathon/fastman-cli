"""
Authentication installation commands.

This module is a dispatcher: it picks the right auth provider, installs
its dependencies, renders the corresponding ``.j2`` templates from
``src/fastman/_templates/auth/<provider>/``, and patches the user's
``app/main.py`` + ``app/core/config.py`` where needed.

The actual generated code (security utilities, models, schemas, routers,
…) lives on disk in the templates package — see those files for what
each provider emits.
"""
from pathlib import Path
from typing import Iterable

from ..console import Output, Style
from ..templates import TemplateLoader
from ..utils import EnvManager, PackageManager, PathManager
from .base import Command, register


# ── OAuth provider catalog ─────────────────────────────────────────────
# Move new providers into this dict; the rest of the OAuth flow is
# driven from the values here.
_OAUTH_PROVIDERS = {
    "google": {
        "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "access_token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://www.googleapis.com/oauth2/v3/userinfo",
        "scopes": "openid email profile",
    },
    "github": {
        "authorize_url": "https://github.com/login/oauth/authorize",
        "access_token_url": "https://github.com/login/oauth/access_token",
        "userinfo_url": "https://api.github.com/user",
        "scopes": "read:user user:email",
    },
    "discord": {
        "authorize_url": "https://discord.com/api/oauth2/authorize",
        "access_token_url": "https://discord.com/api/oauth2/token",
        "userinfo_url": "https://discord.com/api/users/@me",
        "scopes": "identify email",
    },
}


# ── Settings + env block fragments (kept inline — small + injection-bound) ──

_KEYCLOAK_SETTINGS_BLOCK = """
    # Keycloak
    KEYCLOAK_URL: str = "http://localhost:8080"
    KEYCLOAK_REALM: str = "master"
    KEYCLOAK_CLIENT_ID: str = ""
    KEYCLOAK_CLIENT_SECRET: str = ""
    KEYCLOAK_ADMIN_SECRET: str = ""
    KEYCLOAK_CALLBACK_URI: str = "http://localhost:8000/callback"
    KEYCLOAK_VERIFY_SSL: str = "true"
    """

_KEYCLOAK_ENV_BLOCK = """
# Keycloak Authentication
KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=master
KEYCLOAK_CLIENT_ID=your-client-id
KEYCLOAK_CLIENT_SECRET=your-client-secret
KEYCLOAK_ADMIN_SECRET=your-admin-cli-secret
KEYCLOAK_CALLBACK_URI=http://localhost:8000/callback
KEYCLOAK_VERIFY_SSL=true
"""

_PASSKEY_ENV_BLOCK = """
# Passkey / WebAuthn
PASSKEY_RP_ID=localhost
PASSKEY_RP_NAME=Fastman App
PASSKEY_ORIGIN=http://localhost:8000
"""


def _write_rendered(
    target_dir: Path,
    files: Iterable[tuple[str, str, dict]],
) -> None:
    """Render each (template_name, dest_filename, context) and write under target_dir."""
    PathManager.ensure_dir(target_dir)
    for template_name, dest, ctx in files:
        content = TemplateLoader.render(template_name, ctx)
        PathManager.write_file(target_dir / dest, content)


@register
class InstallAuthCommand(Command):
    signature = "install:auth {--type=jwt} {--provider=} {--append-certificate}"
    description = "Install authentication scaffolding (jwt, oauth, keycloak, passkey)"
    help = """
Examples:
  fastman install:auth
  fastman install:auth --type=jwt
  fastman install:auth --type=oauth --provider=google
  fastman install:auth --type=keycloak
  fastman install:auth --type=keycloak --append-certificate
  fastman install:auth --type=passkey
"""

    def handle(self):
        auth_type = self.option("type", "jwt").lower()
        provider = self.option("provider")

        if auth_type == "jwt":
            self._install_jwt()
        elif auth_type == "oauth":
            self._install_oauth(provider)
        elif auth_type == "keycloak":
            self._install_keycloak()
            if self.flag("append-certificate"):
                self._append_certificate()
        elif auth_type == "passkey":
            self._install_passkey()
        else:
            Output.error(f"Unknown auth type: {auth_type}")
            Output.info("Available types: jwt, oauth, keycloak, passkey")

    # ── JWT ─────────────────────────────────────────────────────────

    def _install_jwt(self):
        Output.info("Installing JWT authentication...")

        packages = ["pyjwt", "passlib[bcrypt]", "python-multipart"]
        if not PackageManager.install(packages):
            Output.error("Failed to install dependencies")
            return

        base = Path("app/features/auth")
        _write_rendered(
            base,
            [
                ("auth/jwt/security.py.j2", "security.py", {}),
                ("auth/jwt/models.py.j2", "models.py", {}),
                ("auth/jwt/schemas.py.j2", "schemas.py", {}),
                ("auth/jwt/service.py.j2", "service.py", {}),
                ("auth/jwt/dependencies.py.j2", "dependencies.py", {}),
                ("auth/jwt/router.py.j2", "router.py", {}),
            ],
        )

        Output.success("JWT authentication installed!")
        Output.info("\nEndpoints created:")
        Output.echo("  POST /auth/register - Register new user", Style.GREEN)
        Output.echo("  POST /auth/login - Login user", Style.GREEN)
        Output.echo("  GET  /auth/me - Get current user", Style.GREEN)
        Output.info("\nNext steps:")
        Output.echo("  1. Run: fastman make:migration 'add users table'", Style.CYAN)
        Output.echo("  2. Run: fastman database:migrate", Style.CYAN)
        Output.echo("  3. Test at: http://localhost:8000/docs", Style.CYAN)

    # ── OAuth ───────────────────────────────────────────────────────

    def _install_oauth(self, provider: str | None):
        provider = (provider or "google").lower()
        if provider not in _OAUTH_PROVIDERS:
            Output.error(
                f"Unknown OAuth provider '{provider}'. "
                f"Built-in: {', '.join(sorted(_OAUTH_PROVIDERS))}."
            )
            return

        Output.info(f"Installing OAuth authentication (provider: {provider})...")

        packages = ["authlib", "httpx", "python-multipart"]
        if not PackageManager.install(packages):
            Output.error("Failed to install dependencies")
            return

        cfg = _OAUTH_PROVIDERS[provider]
        ctx = {"provider": provider, **cfg}
        base = Path("app/features/auth")
        _write_rendered(
            base,
            [
                ("auth/oauth/oauth_config.py.j2", "oauth_config.py", ctx),
                ("auth/oauth/models.py.j2", "models.py", {}),
                ("auth/oauth/schemas.py.j2", "schemas.py", {}),
                ("auth/oauth/service.py.j2", "service.py", {}),
                ("auth/oauth/router.py.j2", "router.py", ctx),
            ],
        )

        # Env credentials placeholder
        oauth_env = (
            f"\n# OAuth ({provider})\n"
            f"OAUTH_CLIENT_ID=your-{provider}-client-id\n"
            f"OAUTH_CLIENT_SECRET=your-{provider}-client-secret\n"
        )
        EnvManager.append_to_all(oauth_env, "OAUTH_CLIENT_ID")
        Output.info("Updated env files with OAuth credentials")

        Output.success(f"OAuth authentication installed ({provider})!")
        Output.info("\nEndpoints created:")
        Output.echo("  GET  /auth/login - Redirect to provider", Style.GREEN)
        Output.echo("  GET  /auth/callback - OAuth callback", Style.GREEN)
        Output.echo("  GET  /auth/me - Current user info", Style.GREEN)
        Output.echo("  GET  /auth/logout - Logout", Style.GREEN)
        Output.info("\nNext steps:")
        Output.echo(f"  1. Create a {provider} OAuth app and get Client ID/Secret", Style.CYAN)
        Output.echo("  2. Update .env with your credentials", Style.CYAN)
        Output.echo("  3. Run: fastman make:migration 'add users table'", Style.CYAN)
        Output.echo("  4. Run: fastman database:migrate", Style.CYAN)
        Output.echo("  5. Add SessionMiddleware to app/main.py:", Style.CYAN)
        Output.echo("     from starlette.middleware.sessions import SessionMiddleware", Style.YELLOW)
        Output.echo(
            "     app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)",
            Style.YELLOW,
        )

    # ── Keycloak ────────────────────────────────────────────────────

    def _install_keycloak(self):
        Output.info("Installing Keycloak authentication...")

        core_dir = Path("app/core")
        if not core_dir.exists():
            Output.error("Directory 'app/core' not found.")
            Output.info("Make sure you are in a Fastman project directory.")
            Output.info("Run 'fastman create <project-name>' to create a new project first.")
            return

        packages = ["fastapi-keycloak", "certifi"]
        if not PackageManager.install(packages):
            Output.error("Failed to install dependencies")
            return

        # 1. Render and write the Keycloak module
        content = TemplateLoader.render("auth/keycloak/keycloak.py.j2", {})
        keycloak_path = Path("app/core/keycloak.py")
        if not PathManager.write_file(keycloak_path, content):
            Output.error(f"Failed to create {keycloak_path}")
            return

        # 2. Inject Keycloak settings into config.py
        config_path = Path("app/core/config.py")
        if config_path.exists():
            config_content = config_path.read_text(encoding="utf-8")
            if "KEYCLOAK_URL" not in config_content:
                config_content = config_content.replace(
                    "    # API",
                    _KEYCLOAK_SETTINGS_BLOCK + "\n    # API",
                )
                config_path.write_text(config_content, encoding="utf-8")
                Output.info("Updated config.py with Keycloak settings")

        # 3. Wire init_keycloak() into main.py
        main_path = Path("app/main.py")
        if main_path.exists():
            main_content = main_path.read_text(encoding="utf-8")
            if "from app.core.keycloak import init_keycloak" not in main_content:
                main_content = main_content.replace(
                    "from app.core.logging import setup_logging",
                    "from app.core.logging import setup_logging\n"
                    "from app.core.keycloak import init_keycloak",
                )
                main_content = main_content.replace(
                    "# Health check",
                    "# Initialize Keycloak\ninit_keycloak(app)\n\n# Health check",
                )
                main_path.write_text(main_content, encoding="utf-8")
                Output.info("Updated main.py with Keycloak initialization")

        # 4. Env vars
        EnvManager.append_to_all(_KEYCLOAK_ENV_BLOCK, "KEYCLOAK_URL")
        Output.info("Updated env files with Keycloak configuration")

        Output.success("Keycloak authentication installed!")
        Output.info("\nFiles created/updated:")
        Output.echo("  app/core/keycloak.py - Keycloak configuration & dependencies", Style.GREEN)
        Output.echo("  app/core/config.py - Added Keycloak settings", Style.GREEN)
        Output.echo("  app/main.py - Added Keycloak initialization", Style.GREEN)
        Output.echo("  .env.* - Added Keycloak environment variables", Style.GREEN)
        Output.info("\nEndpoints created:")
        Output.echo("  GET /me - Current authenticated user", Style.GREEN)
        Output.info("\nNext steps:")
        Output.echo("  1. Update .env with your Keycloak credentials", Style.CYAN)
        Output.echo("  2. Restart your server", Style.CYAN)
        Output.echo("  3. Test at: http://localhost:8000/docs (use Authorize button)", Style.CYAN)
        Output.info("\nKeycloak client requirements:")
        Output.echo("  - KEYCLOAK_CLIENT_ID / KEYCLOAK_CLIENT_SECRET: confidential client", Style.YELLOW)
        Output.echo("  - KEYCLOAK_ADMIN_SECRET: optional (admin-cli; leave empty to skip admin features)", Style.YELLOW)
        Output.echo("  - Public admin-cli client → app still starts, admin features disabled", Style.YELLOW)
        Output.info("\nTo protect additional routes:")
        Output.echo("  from fastapi import Depends", Style.YELLOW)
        Output.echo("  from fastapi_keycloak import OIDCUser", Style.YELLOW)
        Output.echo("  from app.core.keycloak import get_current_user", Style.YELLOW)
        Output.echo('  @router.get("/protected")', Style.YELLOW)
        Output.echo("  def protected_route(user: OIDCUser = Depends(get_current_user)):", Style.YELLOW)
        Output.echo('      return {"message": f"Hello, {user.email}"}', Style.YELLOW)

    def _append_certificate(self):
        """Optional follow-up: build the merged SSL bundle from certs/."""
        from .certificate import CERTS_DIR, prepare_certificate_bundle

        Output.new_line()
        Output.info("Certificate bundle preparation requested...")
        if not CERTS_DIR.exists():
            PathManager.ensure_dir(CERTS_DIR)
            init_file = CERTS_DIR / "__init__.py"
            if init_file.exists():
                init_file.unlink()
            Output.info(f"Created {CERTS_DIR}/ directory.")
            Output.echo(
                "  Place your .pem or .crt files there, then run: fastman install:cert",
                Style.CYAN,
            )
        else:
            prepare_certificate_bundle(CERTS_DIR)

    # ── Passkey / WebAuthn ──────────────────────────────────────────

    def _install_passkey(self):
        Output.info("Installing Passkey (WebAuthn) authentication...")

        packages = ["py-webauthn>=2.0.0", "pyjwt", "python-multipart"]
        if not PackageManager.install(packages):
            Output.error("Failed to install dependencies")
            return

        base = Path("app/features/auth")
        _write_rendered(
            base,
            [
                ("auth/passkey/models.py.j2", "models.py", {}),
                ("auth/passkey/schemas.py.j2", "schemas.py", {}),
                ("auth/passkey/service.py.j2", "service.py", {}),
                ("auth/passkey/security.py.j2", "security.py", {}),
                ("auth/passkey/dependencies.py.j2", "dependencies.py", {}),
                ("auth/passkey/router.py.j2", "router.py", {}),
            ],
        )

        EnvManager.append_to_all(_PASSKEY_ENV_BLOCK, "PASSKEY_RP_ID")
        Output.info("Updated env files with Passkey settings")

        Output.success("Passkey (WebAuthn) authentication installed!")
        Output.info("\nNo passwords needed! Users authenticate with:")
        Output.echo("  - Fingerprint", Style.GREEN)
        Output.echo("  - Face ID", Style.GREEN)
        Output.echo("  - Hardware security key (YubiKey)", Style.GREEN)
        Output.echo("  - Device PIN", Style.GREEN)
        Output.info("\nEndpoints created:")
        Output.echo("  POST /auth/passkey/register/options - Start registration", Style.GREEN)
        Output.echo("  POST /auth/passkey/register/verify - Verify registration", Style.GREEN)
        Output.echo("  POST /auth/passkey/authenticate/options - Start login", Style.GREEN)
        Output.echo("  POST /auth/passkey/authenticate/verify - Verify login", Style.GREEN)
        Output.echo("  GET  /auth/passkey/me - Current user", Style.GREEN)
        Output.echo("  GET  /auth/passkey/credentials - List passkeys", Style.GREEN)
        Output.echo("  DELETE /auth/passkey/credentials/{id} - Remove passkey", Style.GREEN)
        Output.info("\nNext steps:")
        Output.echo("  1. Run: fastman make:migration 'add users and passkeys tables'", Style.CYAN)
        Output.echo("  2. Run: fastman database:migrate", Style.CYAN)
        Output.echo("  3. Update .env with your domain (RP_ID, ORIGIN)", Style.CYAN)
        Output.echo("  4. Implement the WebAuthn JS client (see browser API docs)", Style.CYAN)
