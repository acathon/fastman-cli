"""
Unit tests for the v0.4.2 polish-wave commands: route:list --json,
db:fresh production guard, model:show locator.
"""
from __future__ import annotations

import io
import json
import os
import sys
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fastman.commands.base import COMMAND_REGISTRY
import fastman.main  # noqa: F401  — registers all commands


# ── route:list --json ──────────────────────────────────────────────────


class TestRouteListJson:
    """The --json output is the tooling contract; pin its shape."""

    def _run_route_list(self, args: list[str], app):
        """Capture stdout from a route:list invocation with a stubbed app."""
        from fastman.commands.misc import RouteListCommand

        cmd = RouteListCommand(args)
        # Patch the import so we don't need an app/main.py on disk.
        with patch.dict(sys.modules, {"app.main": _StubModule(app)}):
            buf = io.StringIO()
            with redirect_stdout(buf):
                cmd.handle()
            return buf.getvalue()

    def test_json_output_is_valid_json(self):
        app = _make_stub_app([
            ("GET,HEAD", "/health", "health"),
            ("POST", "/users", "create_user"),
        ])
        out = self._run_route_list(["--json"], app)
        parsed = json.loads(out)
        assert isinstance(parsed, list)
        assert len(parsed) == 2

    def test_json_shape_per_route(self):
        app = _make_stub_app([("POST", "/users", "create_user")])
        out = self._run_route_list(["--json"], app)
        parsed = json.loads(out)
        assert parsed[0] == {
            "methods": ["POST"],
            "path": "/users",
            "name": "create_user",
        }

    def test_json_method_filter_combines(self):
        app = _make_stub_app([
            ("GET", "/health", "health"),
            ("POST", "/users", "create_user"),
        ])
        out = self._run_route_list(["--json", "--method=POST"], app)
        parsed = json.loads(out)
        assert len(parsed) == 1
        assert parsed[0]["path"] == "/users"

    def test_json_path_filter_combines(self):
        app = _make_stub_app([
            ("GET", "/health", "health"),
            ("GET", "/api/v1/users", "list_users"),
            ("GET", "/api/v1/orders", "list_orders"),
        ])
        out = self._run_route_list(["--json", "--path=/api/v1"], app)
        parsed = json.loads(out)
        assert {r["path"] for r in parsed} == {"/api/v1/users", "/api/v1/orders"}

    def test_websocket_routes_emit_ws_method(self):
        # FastAPI WebSocket routes have no `methods` attribute (or empty set).
        # _get_routes_from_app marks them as "WS".
        app = _make_stub_app([(None, "/ws/chat", "chat")])
        out = self._run_route_list(["--json"], app)
        parsed = json.loads(out)
        assert parsed[0]["methods"] == ["WS"]


# ── db:fresh production guard ──────────────────────────────────────────


class TestDbFreshGuard:
    """The destructive db:fresh must refuse to run in production."""

    def test_refuses_production_environment(self, monkeypatch, tmp_path: Path):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "alembic.ini").write_text("[alembic]\n")
        monkeypatch.setenv("ENVIRONMENT", "production")

        from fastman.commands.database import DatabaseFreshCommand

        # Run with --force so the interactive prompt path isn't taken;
        # the production guard should still trigger.
        cmd = DatabaseFreshCommand(["--force"])
        buf = io.StringIO()
        with redirect_stdout(buf):
            cmd.handle()

        # We don't shell out to alembic. Easiest verification: ensure no
        # subprocess.run was called for downgrade/upgrade.
        with patch("subprocess.run") as mock_run:
            cmd = DatabaseFreshCommand(["--force"])
            cmd.handle()
            mock_run.assert_not_called()

    def test_alembic_missing_blocks_before_guard_unlocks(self, monkeypatch, tmp_path: Path):
        monkeypatch.chdir(tmp_path)
        # No alembic.ini in cwd → _require_alembic returns False, command exits.
        monkeypatch.setenv("ENVIRONMENT", "develop")

        from fastman.commands.database import DatabaseFreshCommand
        with patch("subprocess.run") as mock_run:
            cmd = DatabaseFreshCommand(["--force"])
            cmd.handle()
            mock_run.assert_not_called()


# ── model:show locator ─────────────────────────────────────────────────


class TestModelShowLocator:
    """Snake_case / Pascal_case input should both resolve the same class."""

    def _make_project(self, root: Path) -> None:
        (root / "app" / "core").mkdir(parents=True)
        (root / "app" / "__init__.py").write_text("")
        (root / "app" / "core" / "__init__.py").write_text("")
        (root / "app" / "core" / "database.py").write_text(
            "from sqlalchemy.orm import DeclarativeBase\n"
            "class Base(DeclarativeBase):\n"
            "    pass\n"
        )
        (root / "app" / "features" / "user_profile").mkdir(parents=True)
        (root / "app" / "features" / "__init__.py").write_text("")
        (root / "app" / "features" / "user_profile" / "__init__.py").write_text("")
        (root / "app" / "features" / "user_profile" / "models.py").write_text(
            "from sqlalchemy import String\n"
            "from sqlalchemy.orm import Mapped, mapped_column\n"
            "from app.core.database import Base\n"
            "class UserProfile(Base):\n"
            "    __tablename__ = 'user_profiles'\n"
            "    id: Mapped[int] = mapped_column(primary_key=True)\n"
            "    name: Mapped[str] = mapped_column(String(100))\n"
        )

    def test_finds_by_pascal_case(self, monkeypatch, tmp_path: Path):
        self._make_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        monkeypatch.syspath_prepend(str(tmp_path))
        # Ensure no cached imports from earlier tests.
        for name in list(sys.modules):
            if name.startswith("app."):
                del sys.modules[name]

        from fastman.commands.database import ModelShowCommand
        cmd = ModelShowCommand([])
        cls = cmd._locate_model("UserProfile")
        assert cls is not None
        assert cls.__name__ == "UserProfile"

    def test_finds_by_snake_case(self, monkeypatch, tmp_path: Path):
        self._make_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        monkeypatch.syspath_prepend(str(tmp_path))
        for name in list(sys.modules):
            if name.startswith("app."):
                del sys.modules[name]

        from fastman.commands.database import ModelShowCommand
        cmd = ModelShowCommand([])
        cls = cmd._locate_model("user_profile")
        assert cls is not None
        assert cls.__name__ == "UserProfile"

    def test_returns_none_when_not_found(self, monkeypatch, tmp_path: Path):
        self._make_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        monkeypatch.syspath_prepend(str(tmp_path))
        for name in list(sys.modules):
            if name.startswith("app."):
                del sys.modules[name]

        from fastman.commands.database import ModelShowCommand
        cmd = ModelShowCommand([])
        assert cmd._locate_model("Nonexistent") is None


# ── Command registration ─────────────────────────────────────────────


class TestCommandsRegistered:
    def test_db_fresh_registered(self):
        assert "db:fresh" in COMMAND_REGISTRY

    def test_model_show_registered(self):
        assert "model:show" in COMMAND_REGISTRY

    def test_route_list_has_json_flag(self):
        cls = COMMAND_REGISTRY["route:list"]
        assert "{--json}" in cls.signature


# ── Helpers ────────────────────────────────────────────────────────────


class _StubRoute:
    def __init__(self, methods: str, path: str, name: str):
        self.path = path
        self.name = name
        if methods is None:
            # WebSocket route — no methods attribute at all in FastAPI.
            pass
        else:
            self.methods = set(methods.split(","))


class _StubApp:
    def __init__(self, routes: list[_StubRoute]):
        self.routes = routes


class _StubModule:
    """Mock for `from app.main import app`."""

    def __init__(self, app):
        self.app = app


def _make_stub_app(spec: list[tuple]) -> _StubApp:
    return _StubApp([_StubRoute(*row) for row in spec])
