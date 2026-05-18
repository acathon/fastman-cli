"""
Mail commands: install transport and scaffold Mailable classes.

`install:mail` is one-shot — adds fastapi-mail, writes app/core/mail.py,
app/mail/base.py, an example template, and provider-specific env vars.

`make:mail` scaffolds one Mailable per call, parallel to make:feature.

Templates live in :mod:`fastman._templates.mail` as ``.j2`` files. The
command modules dispatch + format env vars; the actual code we emit lives
on disk where it can be syntax-highlighted, linted, and reviewed.
"""
from pathlib import Path

from ..console import Output, Style
from ..templates import TemplateLoader
from ..utils import EnvManager, NameValidator, PackageManager, PathManager
from .base import Command, register


# Provider-specific env defaults. The env var keys are the same across all
# providers — what differs is the MAIL_SERVER and a couple of conventions
# (e.g. SendGrid uses the literal username "apikey" with the API key as
# the password).
def _provider_env(provider: str, from_email: str) -> dict:
    defaults = {
        "smtp": {
            "MAIL_USERNAME": "",
            "MAIL_PASSWORD": "",
            "MAIL_FROM": from_email,
            "MAIL_FROM_NAME": "Fastman App",
            "MAIL_SERVER": "smtp.gmail.com",
            "MAIL_PORT": "587",
            "MAIL_STARTTLS": "true",
            "MAIL_SSL_TLS": "false",
            "MAIL_TEMPLATE_FOLDER": "templates/email",
        },
        "sendgrid": {
            "MAIL_USERNAME": "apikey",
            "MAIL_PASSWORD": "",
            "MAIL_FROM": from_email,
            "MAIL_FROM_NAME": "Fastman App",
            "MAIL_SERVER": "smtp.sendgrid.net",
            "MAIL_PORT": "587",
            "MAIL_STARTTLS": "true",
            "MAIL_SSL_TLS": "false",
            "MAIL_TEMPLATE_FOLDER": "templates/email",
        },
        "mailgun": {
            "MAIL_USERNAME": "",
            "MAIL_PASSWORD": "",
            "MAIL_FROM": from_email,
            "MAIL_FROM_NAME": "Fastman App",
            "MAIL_SERVER": "smtp.mailgun.org",
            "MAIL_PORT": "587",
            "MAIL_STARTTLS": "true",
            "MAIL_SSL_TLS": "false",
            "MAIL_TEMPLATE_FOLDER": "templates/email",
        },
        "ses": {
            "MAIL_USERNAME": "",
            "MAIL_PASSWORD": "",
            "MAIL_FROM": from_email,
            "MAIL_FROM_NAME": "Fastman App",
            "MAIL_SERVER": "email-smtp.us-east-1.amazonaws.com",
            "MAIL_PORT": "587",
            "MAIL_STARTTLS": "true",
            "MAIL_SSL_TLS": "false",
            "MAIL_TEMPLATE_FOLDER": "templates/email",
        },
    }
    return defaults.get(provider, defaults["smtp"])


# Block injected into the user's app/core/config.py Settings class. Kept
# inline because it's tiny and bound to the settings-injection logic below.
_SETTINGS_FIELDS = """
    # Mail
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = "noreply@example.com"
    MAIL_FROM_NAME: str = "Fastman App"
    MAIL_SERVER: str = "localhost"
    MAIL_PORT: int = 587
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    MAIL_TEMPLATE_FOLDER: str = "templates/email"
"""


@register
class InstallMailCommand(Command):
    signature = "install:mail {--provider=smtp} {--from=}"
    description = "Install mail scaffolding (smtp, sendgrid, mailgun, ses)"
    help = """
Examples:
  fastman install:mail
  fastman install:mail --provider=sendgrid
  fastman install:mail --provider=mailgun --from=noreply@mydomain.com
  fastman install:mail --provider=ses
"""

    VALID_PROVIDERS = ("smtp", "sendgrid", "mailgun", "ses")

    def handle(self):
        provider = (self.option("provider", "smtp") or "smtp").lower()
        from_email = self.option("from") or "noreply@example.com"

        if provider not in self.VALID_PROVIDERS:
            Output.error(
                f"Invalid provider '{provider}'. Must be one of: {', '.join(self.VALID_PROVIDERS)}"
            )
            return

        core_dir = Path("app/core")
        if not core_dir.exists():
            Output.error("Directory 'app/core' not found.")
            Output.info("Run 'fastman create <project>' first, or 'fastman init' in an existing project.")
            return

        Output.info(f"Installing mail transport (provider: {provider})...")

        # 1. Dependencies
        packages = ["fastapi-mail", "jinja2"]
        if provider == "ses":
            packages.append("boto3")
        if not PackageManager.install(packages):
            Output.error("Failed to install dependencies")
            return

        # 2. Render + write files from _templates/mail/*.j2
        files = {
            Path("app/core/mail.py"): TemplateLoader.render("mail/core_mail.py.j2", {}),
            Path("app/mail/__init__.py"): TemplateLoader.render("mail/__init__.py.j2", {}),
            Path("app/mail/base.py"): TemplateLoader.render("mail/base.py.j2", {}),
            Path("templates/email/welcome.html"): TemplateLoader.render(
                "mail/welcome.html.j2", {}
            ),
        }

        # Ensure dirs that PathManager.write_file would skip (notably templates/email/).
        PathManager.ensure_dir(Path("app/mail"))
        Path("templates/email").mkdir(parents=True, exist_ok=True)

        for path, content in files.items():
            if path.exists():
                Output.warn(f"Skipped existing file: {path}")
                continue
            PathManager.write_file(path, content)

        # 3. Settings injection
        self._inject_settings()

        # 4. Env vars (all .env* files)
        env_block = self._build_env_block(provider, from_email)
        EnvManager.append_to_all(env_block, "MAIL_SERVER")
        Output.info("Updated env files with mail configuration")

        Output.new_line()
        Output.success(f"Mail transport installed ({provider})!")
        Output.info("\nFiles created:")
        Output.echo("  app/core/mail.py     - FastMail client & send helpers", Style.GREEN)
        Output.echo("  app/mail/base.py     - Mailable base class", Style.GREEN)
        Output.echo("  templates/email/     - Email template directory", Style.GREEN)
        Output.info("\nNext steps:")
        Output.echo("  1. Fill in MAIL_USERNAME/MAIL_PASSWORD in .env", Style.CYAN)
        Output.echo("  2. fastman make:mail WelcomeEmail", Style.CYAN)
        Output.echo(
            "  3. In a route: await WelcomeEmail().send(to=['user@example.com'])",
            Style.CYAN,
        )

        if provider == "sendgrid":
            Output.new_line()
            Output.info("SendGrid: set MAIL_PASSWORD to your API key. MAIL_USERNAME stays 'apikey'.")
        elif provider == "ses":
            Output.new_line()
            Output.info("AWS SES: create SMTP credentials in the SES console — they are NOT your IAM keys.")
            Output.info("Update MAIL_SERVER to your region (e.g. email-smtp.eu-west-1.amazonaws.com).")

    def _build_env_block(self, provider: str, from_email: str) -> str:
        env = _provider_env(provider, from_email)
        lines = [f"\n# Mail ({provider})"]
        for key, value in env.items():
            lines.append(f"{key}={value}")
        return "\n".join(lines) + "\n"

    def _inject_settings(self):
        """Add MAIL_* fields to Settings class in app/core/config.py if missing."""
        config_path = Path("app/core/config.py")
        if not config_path.exists():
            Output.warn("app/core/config.py not found — skipping settings injection.")
            return

        content = config_path.read_text(encoding="utf-8")
        if "MAIL_SERVER" in content:
            Output.info("Mail settings already present in config.py — skipped injection.")
            return

        # Prefer the modern SettingsConfigDict marker (Pydantic v2 generated
        # projects), then fall back to the legacy nested ``class Config``,
        # then append before ``settings = Settings()`` as a last resort.
        if "    model_config = SettingsConfigDict(" in content:
            content = content.replace(
                "    model_config = SettingsConfigDict(",
                f"{_SETTINGS_FIELDS}    model_config = SettingsConfigDict(",
            )
        elif "    class Config:" in content:
            content = content.replace(
                "    class Config:", f"{_SETTINGS_FIELDS}    class Config:"
            )
        elif "settings = Settings()" in content:
            content = content.replace(
                "settings = Settings()", f"{_SETTINGS_FIELDS}\nsettings = Settings()"
            )
        else:
            Output.warn(
                "Could not locate injection point in config.py — please add MAIL_* fields manually."
            )
            return

        config_path.write_text(content, encoding="utf-8")
        Output.info("Updated config.py with mail settings")


@register
class MakeMailCommand(Command):
    signature = "make:mail {name} {--markdown} {--subject=}"
    description = "Create a Mailable class for sending a specific email"
    help = """
Examples:
  fastman make:mail WelcomeEmail
  fastman make:mail PasswordReset --subject="Reset your password"
  fastman make:mail OrderShipped --markdown
"""

    def handle(self):
        name = self.prompt_argument(0, "Mailable name")
        name = self.validate_name(name, "Mailable name is required")
        markdown = self.flag("markdown")
        subject = self.option("subject") or NameValidator.to_pascal_case(name)

        mail_dir = Path("app/mail")
        if not mail_dir.exists():
            Output.error("Directory 'app/mail' not found.")
            Output.info("Run 'fastman install:mail' first to set up the mail transport.")
            return

        snake = NameValidator.to_snake_case(name)
        pascal = NameValidator.to_pascal_case(name)

        py_path = mail_dir / f"{snake}.py"
        if py_path.exists():
            Output.error(f"Mailable '{snake}' already exists")
            return

        template_ext = "md" if markdown else "html"
        template_file = f"{snake}.{template_ext}"
        template_path = Path("templates/email") / template_file
        context = {
            "pascal": pascal,
            "subject": subject,
            "template_file": template_file,
        }

        if markdown:
            self._ensure_markdown_it()
            py_content = TemplateLoader.render("mail/mailable_md.py.j2", context)
            tpl_content = TemplateLoader.render("mail/stub.md.j2", context)
        else:
            py_content = TemplateLoader.render("mail/mailable_html.py.j2", context)
            tpl_content = TemplateLoader.render("mail/stub.html.j2", context)

        PathManager.write_file(py_path, py_content)
        if not template_path.exists():
            PathManager.write_file(template_path, tpl_content)
        else:
            Output.warn(f"Template already exists, kept: {template_path}")

        Output.success(f"Mailable '{pascal}' created at {py_path}")
        Output.info(f"Template: {template_path}")
        Output.info("\nUse it:")
        Output.echo(f"  from app.mail.{snake} import {pascal}", Style.CYAN)
        Output.echo(
            f"  await {pascal}(name='Alice').send(to=['user@example.com'])",
            Style.CYAN,
        )

    def _ensure_markdown_it(self):
        """Install markdown-it-py if --markdown is requested and it's missing."""
        try:
            import markdown_it  # noqa: F401
            return
        except ImportError:
            pass
        Output.info("Installing markdown-it-py for Markdown rendering...")
        PackageManager.install(["markdown-it-py"])
