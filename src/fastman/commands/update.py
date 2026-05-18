"""
`fastman update` — diff project files against current fastman templates.

Sees through three layers of decision:

1. **Which files to inspect.** `update.compute_drifts()` walks the
   per-project recipe catalog and renders each template with the
   project's recorded ``.fastmanrc`` shape, returning only files that
   actually differ from what's on disk.
2. **What the user wants done with each.** Either ``--all`` (apply all),
   ``--check`` (just exit non-zero on drift, for CI), or an interactive
   prompt per file.
3. **Whether to actually write.** :func:`update.apply_drift` does the
   filesystem write; this command only invokes it when the user opted in.

The command never touches files fastman did not originate — your own
features, routes, models, schemas are yours.
"""
from __future__ import annotations

import sys
from pathlib import Path

from ..console import HAS_RICH, Output, Style, console
from ..update import Drift, apply_drift, compute_drifts
from .base import Command, register


@register
class UpdateCommand(Command):
    signature = (
        "update {--check} {--all} {--file=} {--auth} {--mail}"
    )
    description = "Re-scaffold fastman-owned files against current templates"
    help = """
Examples:
  fastman update                  Interactive: review each drifted file
  fastman update --check          Report drifts and exit 1 if any (CI-friendly)
  fastman update --all            Apply every drift without prompting
  fastman update --file=app/core/config.py
                                 Update just one specific file
  fastman update --mail           Only the files install:mail generated
  fastman update --auth           Only the files install:auth generated

How it works:
  For each file fastman originally generated (database.py, config.py,
  alembic/env.py, mail/, ...), `update` renders the *current* template
  using your project's recorded .fastmanrc and compares it to what's on
  disk. If they differ, you get a unified diff and pick keep/update.

  Files fastman did not generate (your own features, routes, models) are
  never touched.

  Commit your work before running `update` — there is no rollback.
"""

    def handle(self):
        cwd = Path.cwd()
        check_only = self.flag("check")
        apply_all = self.flag("all")
        single_file = self.option("file")
        only_mail = self.flag("mail")
        only_auth = self.flag("auth")

        # When --mail or --auth is passed, exclude the other scope so the
        # catalog stays narrow. When neither is passed, include both.
        include_auth = (not only_mail) or only_auth
        include_mail = (not only_auth) or only_mail

        drifts = compute_drifts(
            cwd, include_auth=include_auth, include_mail=include_mail
        )

        if single_file:
            drifts = [d for d in drifts if d.relative == single_file]
            if not drifts:
                Output.info(
                    f"No drift for '{single_file}' (or it isn't a fastman-owned file)."
                )
                return

        if not drifts:
            Output.success("Everything in sync with current fastman templates.")
            return

        # --check: just report, exit non-zero
        if check_only:
            Output.warn(f"{len(drifts)} file(s) would change:")
            for d in drifts:
                marker = "[NEW]" if d.missing else "[CHG]"
                Output.echo(f"  {marker} {d.relative}", Style.YELLOW)
            Output.new_line()
            Output.info("Run without --check to review each file interactively.")
            sys.exit(1)

        # Apply path: interactive or --all
        Output.section(
            "Drift detected",
            f"{len(drifts)} fastman-owned file(s) differ from current templates",
        )
        Output.new_line()

        applied = 0
        skipped = 0
        accept_all = apply_all  # flips to True if user picks "all" mid-flow

        for idx, drift in enumerate(drifts, start=1):
            self._print_drift_summary(idx, len(drifts), drift)

            if accept_all:
                apply_drift(drift)
                applied += 1
                Output.success(f"  Updated {drift.relative}")
                continue

            if self.no_interaction:
                # Non-interactive without --all means we cannot prompt.
                # Refuse rather than guessing.
                Output.error(
                    "Interactive prompts unavailable (--no-interaction). "
                    "Use --all to apply everything, --check to just report, "
                    "or run interactively."
                )
                sys.exit(1)

            choice = self._prompt_choice()
            if choice == "u":
                apply_drift(drift)
                applied += 1
                Output.success(f"  Updated {drift.relative}")
            elif choice == "a":
                accept_all = True
                apply_drift(drift)
                applied += 1
                Output.success(f"  Updated {drift.relative} (applying all remaining)")
            elif choice == "k":
                skipped += 1
                Output.info(f"  Kept {drift.relative} unchanged")
            elif choice == "q":
                Output.info("  Stopped at user request.")
                break

        Output.new_line()
        Output.line()
        if applied:
            Output.success(f"Updated {applied} file(s).")
        if skipped:
            Output.info(f"Kept {skipped} file(s) unchanged.")
        Output.info(
            "Re-run `fastman update --check` later to confirm everything is in sync."
        )

    # ── Display + prompting ─────────────────────────────────────────

    def _print_drift_summary(self, idx: int, total: int, drift: Drift) -> None:
        """Show file path, change-counts, and the diff."""
        Output.new_line()
        if HAS_RICH:
            console.print(
                f"[bold cyan]({idx}/{total})[/bold cyan]  "
                f"[highlight]{drift.relative}[/highlight]  "
                f"{self._counts(drift)}"
            )
        else:
            print(f"({idx}/{total})  {drift.relative}  {self._counts(drift)}")

        diff_text = drift.diff
        if HAS_RICH and diff_text.strip():
            # Render diff with simple ANSI: + green, - red, @@ cyan.
            for line in diff_text.split("\n"):
                if line.startswith("+++") or line.startswith("---"):
                    console.print(f"[dim]{line}[/dim]")
                elif line.startswith("+"):
                    console.print(f"[green]{line}[/green]")
                elif line.startswith("-"):
                    console.print(f"[red]{line}[/red]")
                elif line.startswith("@@"):
                    console.print(f"[cyan]{line}[/cyan]")
                else:
                    console.print(f"[dim]{line}[/dim]")
        else:
            print(diff_text)

    def _counts(self, drift: Drift) -> str:
        """Short '+N/-M lines' summary."""
        if drift.missing:
            return f"[green](new file, {len(drift.desired.splitlines())} lines)[/green]"
        adds = subs = 0
        diff = drift.diff
        for line in diff.split("\n"):
            if line.startswith("+") and not line.startswith("+++"):
                adds += 1
            elif line.startswith("-") and not line.startswith("---"):
                subs += 1
        if HAS_RICH:
            return f"[green]+{adds}[/green] [red]-{subs}[/red] lines"
        return f"+{adds} -{subs} lines"

    def _prompt_choice(self) -> str:
        """Read a one-letter response: u/k/a/q."""
        while True:
            response = Output.ask(
                "  [u]pdate, [k]eep, [a]ll remaining, [q]uit",
                "k",
            ).strip().lower()[:1]
            if response in {"u", "k", "a", "q"}:
                return response
            Output.warn("  Please pick one of: u, k, a, q")
