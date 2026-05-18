"""
Unit tests for the AST-aware injection helpers.

These tests are fast (no package installs, no subprocess) and exercise the
contract that `install:auth` and `install:mail` rely on:

  - First-run insertion places markers correctly.
  - Re-running an install replaces the block in place (idempotent).
  - Same body on re-run produces a clean SKIPPED, not a duplicate write.
  - AST validation refuses to write Python files that would no longer parse.
  - Missing-anchor failure leaves the user's file completely untouched.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fastman.injection import (
    InjectionStatus,
    inject_block,
    inject_into_class_body,
)


# ── inject_block ───────────────────────────────────────────────────────


class TestInjectBlock:
    def test_inserts_with_markers_at_fallback_anchor(self, tmp_path: Path):
        p = tmp_path / "main.py"
        p.write_text(
            "from fastapi import FastAPI\n"
            "app = FastAPI()\n"
            "\n"
            "# Health check\n"
            "@app.get('/health')\n"
            "def health():\n"
            "    return {'ok': True}\n"
        )
        res = inject_block(
            p, "mail:init",
            "from app.core.mail import init_mail\ninit_mail(app)",
            fallback_anchor="# Health check",
        )
        assert res.status == InjectionStatus.INSERTED
        out = p.read_text()
        assert "# fastman:mail:init:start" in out
        assert "# fastman:mail:init:end" in out
        assert "init_mail(app)" in out
        # The start marker must come before the health-check comment
        assert out.index("# fastman:mail:init:start") < out.index("# Health check")
        # File still parses
        import ast
        ast.parse(out)

    def test_idempotent_replace_when_markers_present(self, tmp_path: Path):
        p = tmp_path / "main.py"
        p.write_text("app = None\n# Health check\n")
        inject_block(p, "mail:init", "init_mail(app)", fallback_anchor="# Health check")
        res = inject_block(p, "mail:init", "init_mail(app, debug=True)", fallback_anchor="# Health check")
        assert res.status == InjectionStatus.REPLACED
        out = p.read_text()
        assert out.count("# fastman:mail:init:start") == 1
        assert "debug=True" in out
        assert "init_mail(app)" not in out or "init_mail(app, debug=True)" in out

    def test_skipped_when_body_unchanged(self, tmp_path: Path):
        p = tmp_path / "main.py"
        p.write_text("app = None\n# Health check\n")
        inject_block(p, "mail:init", "init_mail(app)", fallback_anchor="# Health check")
        res = inject_block(p, "mail:init", "init_mail(app)", fallback_anchor="# Health check")
        assert res.status == InjectionStatus.SKIPPED

    def test_fails_when_no_markers_and_no_anchor(self, tmp_path: Path):
        p = tmp_path / "main.py"
        original = "app = None\n"
        p.write_text(original)
        res = inject_block(
            p, "mail:init", "init_mail(app)", fallback_anchor="# Health check"
        )
        assert res.status == InjectionStatus.FAILED
        assert "fallback anchor" in res.reason
        # The user's file must be untouched.
        assert p.read_text() == original

    def test_fails_when_injection_breaks_python_syntax(self, tmp_path: Path):
        p = tmp_path / "main.py"
        original = "app = None\n"
        p.write_text(original)
        res = inject_block(
            p, "broken", "def $$$ not python", fallback_anchor="app ="
        )
        assert res.status == InjectionStatus.FAILED
        assert "would break Python parsing" in res.reason
        # Original file untouched
        assert p.read_text() == original

    def test_preserves_indent_at_anchor(self, tmp_path: Path):
        p = tmp_path / "main.py"
        p.write_text(
            "def setup_app():\n"
            "    app = FastAPI()\n"
            "    # mount-here\n"
            "    return app\n"
        )
        res = inject_block(
            p, "mount", "mount_static(app)", fallback_anchor="# mount-here"
        )
        assert res.status == InjectionStatus.INSERTED
        out = p.read_text()
        # The new line should be indented to match the anchor (4 spaces).
        assert "    mount_static(app)" in out
        assert "    # fastman:mount:start" in out


# ── inject_into_class_body ────────────────────────────────────────────


class TestInjectIntoClassBody:
    def test_appends_to_class_body(self, tmp_path: Path):
        p = tmp_path / "config.py"
        p.write_text(
            "class Settings:\n"
            "    PROJECT_NAME: str = 'demo'\n"
            "    SECRET_KEY: str = 'x'\n"
            "\n"
            "settings = Settings()\n"
        )
        res = inject_into_class_body(
            p, "mail:settings", "Settings",
            "MAIL_FROM: str = 'noreply@example.com'\nMAIL_PORT: int = 587",
        )
        assert res.status == InjectionStatus.INSERTED
        out = p.read_text()
        # Block must land inside the class, before `settings = Settings()`.
        class_block_end = out.index("settings = Settings()")
        assert out.index("MAIL_FROM") < class_block_end
        # Indented at class body indent (4 spaces).
        assert "    MAIL_FROM: str = 'noreply@example.com'" in out
        # File still parses.
        import ast
        ast.parse(out)

    def test_idempotent_on_second_run(self, tmp_path: Path):
        p = tmp_path / "config.py"
        p.write_text(
            "class Settings:\n"
            "    X: int = 1\n"
            "\n"
            "settings = Settings()\n"
        )
        inject_into_class_body(p, "mail:settings", "Settings", "Y: int = 2")
        res = inject_into_class_body(p, "mail:settings", "Settings", "Y: int = 99")
        assert res.status == InjectionStatus.REPLACED
        out = p.read_text()
        assert out.count("# fastman:mail:settings:start") == 1
        assert "Y: int = 99" in out

    def test_fails_on_missing_class(self, tmp_path: Path):
        p = tmp_path / "config.py"
        original = "class NotSettings:\n    X: int = 1\n"
        p.write_text(original)
        res = inject_into_class_body(p, "x", "Settings", "Y: int = 2")
        assert res.status == InjectionStatus.FAILED
        assert "class 'Settings' not found" in res.reason
        assert p.read_text() == original

    def test_fails_on_unparseable_source(self, tmp_path: Path):
        p = tmp_path / "config.py"
        original = "class Settings:\n    def broken("  # SyntaxError
        p.write_text(original)
        res = inject_into_class_body(p, "x", "Settings", "Y: int = 2")
        assert res.status == InjectionStatus.FAILED
        assert "cannot parse Python" in res.reason
        # User's file untouched.
        assert p.read_text() == original


# ── Realistic end-to-end shape ────────────────────────────────────────


class TestRealConfigShape:
    """Smoke-tests against the actual generated config.py shape v0.4.0 emits."""

    GENERATED_CONFIG = '''"""Application configuration"""
import os
from pathlib import Path
from typing import List, Optional

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings (Pydantic v2)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    # Project
    PROJECT_NAME: str = "demo"
    SECRET_KEY: str = "xxx"


settings = Settings()
'''

    def test_mail_injection_into_real_config(self, tmp_path: Path):
        p = tmp_path / "config.py"
        p.write_text(self.GENERATED_CONFIG)
        from fastman.commands.mail import _SETTINGS_FIELDS

        res = inject_into_class_body(p, "mail:settings", "Settings", _SETTINGS_FIELDS)
        assert res.status == InjectionStatus.INSERTED
        out = p.read_text()
        import ast
        ast.parse(out)
        # Mail fields present, settings_dict still there, class still well-formed
        assert "MAIL_FROM: str" in out
        assert "model_config = SettingsConfigDict" in out
        assert "settings = Settings()" in out

    def test_re_running_install_does_not_duplicate(self, tmp_path: Path):
        p = tmp_path / "config.py"
        p.write_text(self.GENERATED_CONFIG)
        from fastman.commands.mail import _SETTINGS_FIELDS

        inject_into_class_body(p, "mail:settings", "Settings", _SETTINGS_FIELDS)
        inject_into_class_body(p, "mail:settings", "Settings", _SETTINGS_FIELDS)
        inject_into_class_body(p, "mail:settings", "Settings", _SETTINGS_FIELDS)
        out = p.read_text()
        assert out.count("# fastman:mail:settings:start") == 1
        assert out.count("MAIL_FROM: str") == 1

    def test_user_customized_config_still_works(self, tmp_path: Path):
        """The pre-AST install used to break when the user renamed `# API`.
        The new injector should still work — it doesn't look for that anchor."""
        customized = '''
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "demo"
    # ===== Application config =====
    SECRET_KEY: str = "xxx"


settings = Settings()
'''
        p = tmp_path / "config.py"
        p.write_text(customized)
        from fastman.commands.mail import _SETTINGS_FIELDS
        res = inject_into_class_body(p, "mail:settings", "Settings", _SETTINGS_FIELDS)
        assert res.status == InjectionStatus.INSERTED
        out = p.read_text()
        import ast
        ast.parse(out)
        assert "MAIL_FROM" in out
