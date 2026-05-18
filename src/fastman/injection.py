"""
AST-aware code injection helpers.

`install:auth` and `install:mail` need to splice new lines into the user's
``app/main.py`` and ``app/core/config.py``. The naive approach is
``content.replace("    # API", ...)``, which silently no-ops the moment the
user renames a comment or reorders an import.

This module provides a hybrid strategy:

1. **Marker-bracket blocks**: each injectable region is delimited by a pair
   of sentinel comments::

       # fastman:mail:settings:start
       MAIL_FROM: str = "..."
       # fastman:mail:settings:end

   When markers are present, re-running an install rewrites the block in
   place (idempotent). When they are absent, fastman falls back to an
   AST-aware insertion that locates a structural target (end of a class
   body, after the last import, before a specific function call) and
   wraps the new block in fresh markers.

2. **Parse before write**: every injection ``ast.parse``-s the result.
   If the post-injection file is no longer valid Python, the write is
   aborted and the user gets a clear error pointing at the source line
   that wouldn't parse. Their original file is never corrupted.

3. **Explicit failure**: there is no silent "marker not found, did
   nothing" path. Every injection returns a status the caller can react
   to and the CLI surfaces.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class InjectionStatus(Enum):
    """Outcome of an injection attempt."""

    INSERTED = "inserted"      # Block inserted for the first time
    REPLACED = "replaced"      # Existing markers found; block replaced
    SKIPPED = "skipped"        # Block already present and unchanged
    FAILED = "failed"          # Could not safely inject (with reason)


@dataclass
class InjectionResult:
    status: InjectionStatus
    reason: str = ""

    @property
    def ok(self) -> bool:
        return self.status in (
            InjectionStatus.INSERTED,
            InjectionStatus.REPLACED,
            InjectionStatus.SKIPPED,
        )


# ── Marker helpers ──────────────────────────────────────────────────────


def _start_marker(tag: str, indent: str = "") -> str:
    return f"{indent}# fastman:{tag}:start"


def _end_marker(tag: str, indent: str = "") -> str:
    return f"{indent}# fastman:{tag}:end"


def _find_block(content: str, tag: str) -> Optional[tuple[int, int, str]]:
    """Locate a marker-delimited block.

    Returns (start_line_idx, end_line_idx_inclusive, indent) if both
    markers are present in order, else None. The indent matches what
    appears on the start marker so the replacement can preserve it.
    """
    lines = content.splitlines()
    start_idx = end_idx = None
    indent = ""

    start_token = f"# fastman:{tag}:start"
    end_token = f"# fastman:{tag}:end"

    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped == start_token and start_idx is None:
            start_idx = i
            indent = line[: len(line) - len(stripped)]
        elif stripped == end_token and start_idx is not None and end_idx is None:
            end_idx = i
            break

    if start_idx is None or end_idx is None:
        return None
    return start_idx, end_idx, indent


def _validate(content: str, path: Path) -> Optional[str]:
    """Return an error message if `content` doesn't parse as Python, else None.

    Only used on files we know are supposed to be Python (.py). Templates
    and config files (.env, .ini) skip this check.
    """
    if path.suffix != ".py":
        return None
    try:
        ast.parse(content)
        return None
    except SyntaxError as exc:
        return f"{path}: would break Python parsing at line {exc.lineno}: {exc.msg}"


# ── Public API ──────────────────────────────────────────────────────────


def inject_block(
    path: Path,
    tag: str,
    block: str,
    *,
    fallback_anchor: Optional[str] = None,
    fallback_position: str = "before",
) -> InjectionResult:
    """Insert or replace a marker-delimited block in `path`.

    Parameters
    ----------
    path: target file (must exist).
    tag: short identifier for the marker pair, e.g. ``"mail:settings"``.
    block: the lines to wrap with markers. Leading/trailing whitespace
        is normalized; do not include marker comments yourself.
    fallback_anchor: when no existing markers are found, insert ``block``
        relative to the first line containing this substring. If the
        anchor is also missing, the injection fails.
    fallback_position: ``"before"`` (default) or ``"after"`` the anchor line.

    Returns
    -------
    :class:`InjectionResult` describing what happened.
    """
    if not path.exists():
        return InjectionResult(InjectionStatus.FAILED, f"{path}: file not found")

    content = path.read_text(encoding="utf-8")
    block_body = block.strip("\n")

    # Case 1: markers present → replace between them.
    existing = _find_block(content, tag)
    if existing is not None:
        start, end, indent = existing
        new_block_lines = [
            _start_marker(tag, indent),
            *_apply_indent(block_body, indent),
            _end_marker(tag, indent),
        ]
        lines = content.splitlines(keepends=False)
        rebuilt = "\n".join(lines[:start] + new_block_lines + lines[end + 1 :])
        if not content.endswith("\n"):
            new_content = rebuilt
        else:
            new_content = rebuilt + "\n"

        if new_content == content:
            return InjectionResult(InjectionStatus.SKIPPED, "block unchanged")

        err = _validate(new_content, path)
        if err:
            return InjectionResult(InjectionStatus.FAILED, err)
        path.write_text(new_content, encoding="utf-8")
        return InjectionResult(InjectionStatus.REPLACED)

    # Case 2: no markers, try the fallback anchor.
    if fallback_anchor is None:
        return InjectionResult(
            InjectionStatus.FAILED,
            f"{path}: markers for '{tag}' not found and no fallback anchor provided",
        )

    lines = content.splitlines(keepends=False)
    anchor_idx = next(
        (i for i, line in enumerate(lines) if fallback_anchor in line),
        None,
    )
    if anchor_idx is None:
        return InjectionResult(
            InjectionStatus.FAILED,
            f"{path}: neither markers nor fallback anchor "
            f"{fallback_anchor!r} were found — please add markers manually "
            f"or open an issue if fastman should support your file shape",
        )

    # Detect the anchor line's indent so block lines line up.
    indent_chars = lines[anchor_idx][: len(lines[anchor_idx]) - len(lines[anchor_idx].lstrip())]
    insertion = [
        _start_marker(tag, indent_chars),
        *_apply_indent(block_body, indent_chars),
        _end_marker(tag, indent_chars),
    ]
    insert_at = anchor_idx if fallback_position == "before" else anchor_idx + 1
    rebuilt_lines = lines[:insert_at] + insertion + lines[insert_at:]
    new_content = "\n".join(rebuilt_lines)
    if content.endswith("\n"):
        new_content += "\n"

    err = _validate(new_content, path)
    if err:
        return InjectionResult(InjectionStatus.FAILED, err)
    path.write_text(new_content, encoding="utf-8")
    return InjectionResult(InjectionStatus.INSERTED)


def inject_into_class_body(
    path: Path,
    tag: str,
    class_name: str,
    block: str,
) -> InjectionResult:
    """Insert a marker-block at the end of a named class body.

    Used when no convenient anchor comment exists (e.g. injecting fields
    into a Pydantic ``Settings`` class). Parses the file with ``ast``,
    locates the target class, and appends ``block`` just before the
    class's ``end_lineno``.

    Idempotent via the marker pair — same semantics as :func:`inject_block`.
    """
    if not path.exists():
        return InjectionResult(InjectionStatus.FAILED, f"{path}: file not found")

    content = path.read_text(encoding="utf-8")

    # If markers are already present, just delegate to the block-based path.
    if _find_block(content, tag) is not None:
        return inject_block(path, tag, block)

    try:
        tree = ast.parse(content)
    except SyntaxError as exc:
        return InjectionResult(
            InjectionStatus.FAILED,
            f"{path}: cannot parse Python at line {exc.lineno}: {exc.msg}",
        )

    target_class = next(
        (
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef) and node.name == class_name
        ),
        None,
    )
    if target_class is None or target_class.end_lineno is None:
        return InjectionResult(
            InjectionStatus.FAILED,
            f"{path}: class '{class_name}' not found",
        )

    lines = content.splitlines(keepends=False)
    insert_idx = target_class.end_lineno  # 1-based; we want to insert *after* this index
    # ast end_lineno is 1-based and inclusive of the last line of the class body.
    # Inserting at lines[insert_idx:] places the block right after the class.
    # That's not what we want for "end of class body"; we want it indented
    # with the class members. Walk back to find the class's body indent.
    body_indent = _detect_body_indent(lines, target_class) or "    "

    insertion = [
        _start_marker(tag, body_indent),
        *_apply_indent(block.strip("\n"), body_indent),
        _end_marker(tag, body_indent),
    ]

    new_lines = lines[:insert_idx] + insertion + lines[insert_idx:]
    new_content = "\n".join(new_lines)
    if content.endswith("\n"):
        new_content += "\n"

    err = _validate(new_content, path)
    if err:
        return InjectionResult(InjectionStatus.FAILED, err)
    path.write_text(new_content, encoding="utf-8")
    return InjectionResult(InjectionStatus.INSERTED)


# ── Internal helpers ────────────────────────────────────────────────────


def _apply_indent(block: str, indent: str) -> list[str]:
    """Return `block` split into lines with `indent` prepended to each non-empty line.

    Empty lines stay empty (no trailing whitespace).
    """
    return [(indent + line) if line.strip() else "" for line in block.split("\n")]


def _detect_body_indent(lines: list[str], class_node: ast.ClassDef) -> Optional[str]:
    """Detect the indent of `class_node`'s first body statement.

    Returns the literal indent string (``"    "`` or ``"\\t"``) or None
    if we can't tell.
    """
    if not class_node.body:
        return None
    first_stmt = class_node.body[0]
    if first_stmt.lineno - 1 >= len(lines):
        return None
    line = lines[first_stmt.lineno - 1]
    return line[: len(line) - len(line.lstrip())]
