"""
Mail commands: install transport and scaffold Mailable classes.

`install:mail` is one-shot — adds fastapi-mail, writes app/core/mail.py,
app/mail/base.py, an example template, and provider-specific env vars.

`make:mail` scaffolds one Mailable per call, parallel to make:feature.
"""
from pathlib import Path
from typing import Optional

from .base import Command, register
from ..console import Output, Style
from ..utils import EnvManager, NameValidator, PackageManager, PathManager


# ── Templates ────────────────────────────────────────────────────────────
# Kept inline for now; if this file grows past ~600 lines, extract to
# templates.py the way the roadmap calls for on auth.py.


_MAIL_CORE = '''"""Mail transport configured at startup.

The FastMail instance is built once from settings and reused for every
send. Mailable subclasses call `send_mail()` / `send_mail_background()`
rather than touching fastmail directly.
"""
from pathlib import Path
from typing import Iterable, Optional

from fastapi import BackgroundTasks
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from app.core.config import settings


def _connection_config() -> ConnectionConfig:
    template_folder = Path(settings.MAIL_TEMPLATE_FOLDER)
    template_folder.mkdir(parents=True, exist_ok=True)
    return ConnectionConfig(
        MAIL_USERNAME=settings.MAIL_USERNAME,
        MAIL_PASSWORD=settings.MAIL_PASSWORD,
        MAIL_FROM=settings.MAIL_FROM,
        MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
        MAIL_PORT=settings.MAIL_PORT,
        MAIL_SERVER=settings.MAIL_SERVER,
        MAIL_STARTTLS=settings.MAIL_STARTTLS,
        MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
        USE_CREDENTIALS=bool(settings.MAIL_USERNAME),
        VALIDATE_CERTS=True,
        TEMPLATE_FOLDER=template_folder,
    )


mail_client = FastMail(_connection_config())


async def send_mail(
    *,
    subject: str,
    recipients: Iterable[str],
    body: Optional[str] = None,
    template_name: Optional[str] = None,
    context: Optional[dict] = None,
    subtype: MessageType = MessageType.html,
    cc: Optional[Iterable[str]] = None,
    bcc: Optional[Iterable[str]] = None,
    attachments: Optional[list] = None,
) -> None:
    """Send synchronously. Use send_mail_background() inside request handlers."""
    message = MessageSchema(
        subject=subject,
        recipients=list(recipients),
        cc=list(cc) if cc else [],
        bcc=list(bcc) if bcc else [],
        body=body or "",
        subtype=subtype,
        attachments=attachments or [],
    )
    if template_name:
        await mail_client.send_message(message, template_name=template_name)
    else:
        await mail_client.send_message(message)


def send_mail_background(background_tasks: BackgroundTasks, **kwargs) -> None:
    """Queue a send via FastAPI's BackgroundTasks (runs after response)."""
    background_tasks.add_task(send_mail, **kwargs)
'''


_MAIL_BASE = '''"""Mailable base class — each email type subclasses this.

Subclasses set `subject`, `template`, and override `context()` to provide
template variables. Use either `.send(to=[...])` (synchronous, awaitable)
or `.send_later(background_tasks, to=[...])` (queued).
"""
from typing import Iterable, Optional

from fastapi import BackgroundTasks
from fastapi_mail import MessageType

from app.core.mail import send_mail, send_mail_background


class Mailable:
    """Base class for all email types."""

    subject: str = ""
    template: Optional[str] = None
    subtype: MessageType = MessageType.html

    def context(self) -> dict:
        """Override to provide template variables."""
        return {}

    async def send(
        self,
        to: Iterable[str],
        cc: Optional[Iterable[str]] = None,
        bcc: Optional[Iterable[str]] = None,
    ) -> None:
        await send_mail(
            subject=self.subject,
            recipients=to,
            cc=cc,
            bcc=bcc,
            template_name=self.template,
            context=self.context(),
            subtype=self.subtype,
        )

    def send_later(
        self,
        background_tasks: BackgroundTasks,
        to: Iterable[str],
        cc: Optional[Iterable[str]] = None,
        bcc: Optional[Iterable[str]] = None,
    ) -> None:
        send_mail_background(
            background_tasks,
            subject=self.subject,
            recipients=to,
            cc=cc,
            bcc=bcc,
            template_name=self.template,
            context=self.context(),
            subtype=self.subtype,
        )
'''


_MAIL_INIT = '''"""Mailables live here. Import them where you want to send."""
from .base import Mailable

__all__ = ["Mailable"]
'''


_WELCOME_TEMPLATE = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Welcome</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 600px; margin: 0 auto; padding: 2rem;">
    <h1>Welcome, {{ name }}!</h1>
    <p>Thanks for signing up. We're glad to have you on board.</p>
    <p>If you have any questions, just reply to this email.</p>
    <hr>
    <p style="color: #888; font-size: 0.85rem;">Sent by Fastman.</p>
</body>
</html>
'''


def _provider_env(provider: str, from_email: str) -> dict:
    """Provider-specific env defaults. Returns dict of (key, value)."""
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


def _settings_fields() -> str:
    """The block injected into app/core/config.py Settings class."""
    return '''
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
'''


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

        # 2. Files
        files = {
            Path("app/core/mail.py"): _MAIL_CORE,
            Path("app/mail/__init__.py"): _MAIL_INIT,
            Path("app/mail/base.py"): _MAIL_BASE,
            Path("templates/email/welcome.html"): _WELCOME_TEMPLATE,
        }

        # Ensure parent dirs (PathManager.write_file does this, but we want
        # the templates/email dir specifically tracked).
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
        Output.echo(f"  1. Fill in MAIL_USERNAME/MAIL_PASSWORD in .env", Style.CYAN)
        Output.echo(f"  2. fastman make:mail WelcomeEmail", Style.CYAN)
        Output.echo(f"  3. In a route: await WelcomeEmail().send(to=['user@example.com'])", Style.CYAN)

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

        fields = _settings_fields()
        # Prefer to inject before the inner Config class, else append before the
        # `settings = Settings()` line. Both injection points are conventional
        # in the generated config.py.
        if "    class Config:" in content:
            content = content.replace("    class Config:", f"{fields}    class Config:")
        elif "settings = Settings()" in content:
            content = content.replace(
                "settings = Settings()", f"{fields}\nsettings = Settings()"
            )
        else:
            Output.warn(
                "Could not locate injection point in config.py — please add MAIL_* fields manually."
            )
            return

        config_path.write_text(content, encoding="utf-8")
        Output.info("Updated config.py with mail settings")


_MAILABLE_TEMPLATE = '''"""Mailable: {pascal}"""
from app.mail.base import Mailable


class {pascal}(Mailable):
    """Override `context()` to inject template variables."""

    subject = "{subject}"
    template = "{template_file}"

    def __init__(self, *, name: str = ""):
        self.name = name

    def context(self) -> dict:
        return {{
            "name": self.name,
        }}
'''


_MAILABLE_TEMPLATE_MD = '''"""Mailable: {pascal} (Markdown-rendered)"""
from pathlib import Path

from markdown_it import MarkdownIt
from fastapi_mail import MessageType

from app.mail.base import Mailable


_md = MarkdownIt()


class {pascal}(Mailable):
    """Markdown body is rendered to HTML at send time.

    Place your Markdown source at `templates/email/{template_file}`.
    """

    subject = "{subject}"
    template = None
    subtype = MessageType.html

    def __init__(self, *, name: str = ""):
        self.name = name

    def context(self) -> dict:
        return {{
            "name": self.name,
        }}

    async def send(self, to, cc=None, bcc=None):
        from app.core.config import settings
        from app.core.mail import send_mail

        src = Path(settings.MAIL_TEMPLATE_FOLDER) / "{template_file}"
        markdown_body = src.read_text(encoding="utf-8")
        for key, value in self.context().items():
            markdown_body = markdown_body.replace("{{{{ " + key + " }}}}", str(value))
        html_body = _md.render(markdown_body)

        await send_mail(
            subject=self.subject,
            recipients=to,
            cc=cc,
            bcc=bcc,
            body=html_body,
            subtype=self.subtype,
        )
'''


_HTML_STUB = '''<!DOCTYPE html>
<html>
<body style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 2rem;">
    <h1>{pascal}</h1>
    <p>Hello {{{{ name }}}},</p>
    <p>This is your {pascal} email. Edit me at <code>templates/email/{template_file}</code>.</p>
</body>
</html>
'''


_MD_STUB = '''# {pascal}

Hello {{{{ name }}}},

This is your **{pascal}** email rendered from Markdown.

Edit me at `templates/email/{template_file}`.

---

_Sent by Fastman._
'''


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
        name = self.validate_name(self.argument(0), "Mailable name is required")
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

        if markdown:
            self._ensure_markdown_it()
            py_content = _MAILABLE_TEMPLATE_MD.format(
                pascal=pascal, subject=subject, template_file=template_file
            )
            tpl_content = _MD_STUB.format(pascal=pascal, template_file=template_file)
        else:
            py_content = _MAILABLE_TEMPLATE.format(
                pascal=pascal, subject=subject, template_file=template_file
            )
            tpl_content = _HTML_STUB.format(pascal=pascal, template_file=template_file)

        PathManager.write_file(py_path, py_content)
        if not template_path.exists():
            PathManager.write_file(template_path, tpl_content)
        else:
            Output.warn(f"Template already exists, kept: {template_path}")

        Output.success(f"Mailable '{pascal}' created at {py_path}")
        Output.info(f"Template: {template_path}")
        Output.info("\nUse it:")
        Output.echo(f"  from app.mail.{snake} import {pascal}", Style.CYAN)
        Output.echo(f"  await {pascal}(name='Alice').send(to=['user@example.com'])", Style.CYAN)

    def _ensure_markdown_it(self):
        """Install markdown-it-py if --markdown is requested and it's missing."""
        try:
            import markdown_it  # noqa: F401
            return
        except ImportError:
            pass
        Output.info("Installing markdown-it-py for Markdown rendering...")
        PackageManager.install(["markdown-it-py"])
