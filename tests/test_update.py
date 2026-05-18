"""
Unit tests for `fastman update` drift detection.

Contracts these tests pin down:

- A just-created project has zero drifts (the catalog renders to the
  same bytes the create command wrote).
- A modified file shows up as drifted, with the on-disk content
  intact in `Drift.current`.
- A missing file shows up with `missing=True`.
- `apply_drift` actually writes the new contents.
- Detection still works with the legacy `.fastman` config missing
  (filesystem inference for pre-0.4.0 projects).
- `include_auth=False` / `include_mail=False` narrow the catalog.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fastman.update import (
    Drift,
    apply_drift,
    compute_drifts,
    core_recipes,
    mail_recipes,
)


def _make_project(
    root: Path,
    *,
    database: str = "sqlite",
    pattern: str = "feature",
    with_mail: bool = False,
) -> None:
    """Build the minimum filesystem shape a project must have for update.

    We don't run `fastman create` here — that's slow and pulls in package
    installs. Instead we render each recipe directly with the **same**
    context :func:`compute_drifts` will later use, so a fresh project
    starts at zero drift.
    """
    from fastman import __version__
    from fastman.update import core_recipes as _core, mail_recipes as _mail

    (root / ".fastmanrc").write_text(
        json.dumps({"pattern": pattern, "package_manager": "pip", "database": database}),
        encoding="utf-8",
    )
    # Match the context shape compute_drifts builds — see update.py.
    ctx = {
        "project_name": root.name,
        "version": __version__,
        "secret_key": "<see-your-.env>",
        "database": database,
    }
    recipes = list(_core(database))
    if with_mail:
        # Mail's filesystem footprint: presence of app/core/mail.py is the
        # trigger for `_has_mail()`. Scaffolding it manually here.
        recipes.extend(_mail())
    for recipe in recipes:
        dest = root / recipe.dest
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(recipe.render(ctx), encoding="utf-8")


class TestComputeDrifts:
    def test_fresh_project_has_no_drift(self, tmp_path: Path):
        proj = tmp_path / "demo"
        proj.mkdir()
        _make_project(proj)

        drifts = compute_drifts(proj)
        assert drifts == [], (
            f"A just-scaffolded project should have zero drifts, "
            f"got {len(drifts)}: {[d.relative for d in drifts]}"
        )

    def test_modified_file_is_detected(self, tmp_path: Path):
        proj = tmp_path / "demo"
        proj.mkdir()
        _make_project(proj)

        target = proj / "app/core/database.py"
        target.write_text("# user changed this entirely\n", encoding="utf-8")

        drifts = compute_drifts(proj)
        assert len(drifts) == 1
        assert drifts[0].relative == "app/core/database.py"
        assert drifts[0].current == "# user changed this entirely\n"
        assert "DeclarativeBase" in drifts[0].desired  # the current template
        assert drifts[0].missing is False

    def test_missing_file_is_detected_as_new(self, tmp_path: Path):
        proj = tmp_path / "demo"
        proj.mkdir()
        _make_project(proj)

        (proj / "app/core/logging.py").unlink()

        drifts = compute_drifts(proj)
        relatives = [d.relative for d in drifts]
        assert "app/core/logging.py" in relatives
        missing_drift = next(d for d in drifts if d.relative == "app/core/logging.py")
        assert missing_drift.missing is True
        assert missing_drift.current == ""
        assert missing_drift.desired  # has content

    def test_apply_drift_writes_file(self, tmp_path: Path):
        proj = tmp_path / "demo"
        proj.mkdir()
        _make_project(proj)

        target = proj / "app/core/database.py"
        target.write_text("# stale\n", encoding="utf-8")

        drifts = compute_drifts(proj)
        assert len(drifts) == 1
        apply_drift(drifts[0])

        # Re-reading should yield the rendered template now.
        assert "DeclarativeBase" in target.read_text(encoding="utf-8")
        # And a second compute_drifts call should find nothing.
        assert compute_drifts(proj) == []

    def test_apply_drift_creates_missing_parent_dirs(self, tmp_path: Path):
        proj = tmp_path / "demo"
        proj.mkdir()
        _make_project(proj)

        # Remove the whole alembic/ directory; apply_drift must recreate it.
        import shutil
        shutil.rmtree(proj / "alembic")

        drifts = compute_drifts(proj)
        alembic_drifts = [d for d in drifts if d.relative.startswith("alembic/")]
        assert len(alembic_drifts) >= 2  # env.py + script.py.mako
        for d in alembic_drifts:
            assert d.missing
            apply_drift(d)
            assert d.path.exists()

    def test_postgresql_renders_correctly(self, tmp_path: Path):
        proj = tmp_path / "demo"
        proj.mkdir()
        _make_project(proj, database="postgresql")

        # Just-rendered postgres project should have zero drifts.
        assert compute_drifts(proj) == []

        # Sanity-check the rendered config has the postgres-specific block.
        config = (proj / "app/core/config.py").read_text(encoding="utf-8")
        assert "postgresql://" in config
        assert "DeclarativeBase" in (proj / "app/core/database.py").read_text(encoding="utf-8")

    def test_firebase_skips_alembic(self, tmp_path: Path):
        proj = tmp_path / "demo"
        proj.mkdir()
        _make_project(proj, database="firebase")

        drifts = compute_drifts(proj)
        # No alembic files expected to drift since they don't exist for firebase.
        assert all(not d.relative.startswith("alembic") for d in drifts)
        assert (proj / "app/core/firebase.py").exists()

    def test_no_fastmanrc_falls_back_to_filesystem_inference(self, tmp_path: Path):
        """Pre-0.4.0 projects don't have .fastmanrc; update should still work."""
        proj = tmp_path / "demo"
        proj.mkdir()
        _make_project(proj, database="sqlite")
        # Drop .fastmanrc so the next call has to infer.
        (proj / ".fastmanrc").unlink()

        drifts = compute_drifts(proj)
        # Still zero drifts because the catalog matches what's on disk.
        assert drifts == []

    def test_no_database_known_returns_empty(self, tmp_path: Path):
        """Projects we can't introspect at all are silently skipped."""
        proj = tmp_path / "empty"
        proj.mkdir()
        # No .fastmanrc, no database.py, no firebase.py — can't tell shape.
        assert compute_drifts(proj) == []


class TestScopeFilters:
    def test_include_mail_false_skips_mail_recipes(self, tmp_path: Path):
        proj = tmp_path / "demo"
        proj.mkdir()
        _make_project(proj, with_mail=True)

        # Modify a mail file so it would normally drift.
        (proj / "app/core/mail.py").write_text("# changed\n", encoding="utf-8")

        # Default: mail file shows up as drift.
        drifts = compute_drifts(proj)
        relatives = {d.relative for d in drifts}
        assert "app/core/mail.py" in relatives

        # With include_mail=False, mail.py is skipped.
        drifts = compute_drifts(proj, include_mail=False)
        relatives = {d.relative for d in drifts}
        assert "app/core/mail.py" not in relatives


class TestRecipeCatalog:
    """Counts the catalog returns for each project shape — a regression guard."""

    def test_sqlite_recipe_count(self):
        # main, config, logging, discovery, gitignore, database, alembic env/ini/mako = 9
        assert len(core_recipes("sqlite")) == 9

    def test_firebase_recipe_count(self):
        # main, config, logging, discovery, gitignore, firebase = 6 (no alembic)
        assert len(core_recipes("firebase")) == 6

    def test_mail_recipe_count(self):
        # core_mail, __init__, base = 3
        assert len(mail_recipes()) == 3
