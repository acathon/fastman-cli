---
sidebar_position: 2
---

# What's New

Stay up to date with the latest Fastman releases and features.

---

## v0.3.0 — February 2026

**Performance improvements and Laravel-style CLI output**

### Highlights

- ⚡ **Performance Boost** — Cached package manager detection
- 🛡️ **Improved Reliability** — Better error handling and timeouts
- 📚 **New Documentation** — Completely rewritten docs site

---

### New Features

#### Clean CLI Output

The CLI now uses clean ASCII symbols instead of Unicode emojis, matching Laravel's professional aesthetic:

```bash
> Creating new project...
> Installing dependencies...
> Project created successfully!

x Error: Could not connect to database
! Warning: No .env file found
```

#### Tinker Improvements

The interactive shell now has better IPython integration:
- Syntax highlighting out of the box
- Tab completion for models and queries
- Magic commands for timing and history

---

### Performance

#### Cached Package Manager Detection

Package manager detection is now cached per session, reducing startup time for subsequent commands:

```python
# Before: Detected on every command (~50ms overhead)
# After:  Detected once, cached in memory
```

---

### Bug Fixes

| Fix | Description |
|-----|-------------|
| **sys.path cleanup** | Commands no longer pollute Python's module path |
| **Subprocess timeouts** | All subprocess calls now have 60-300s timeouts |
| **requirements.txt** | Fixed newline handling when adding packages |
| **CacheClearCommand** | Safer directory traversal during cache clearing |
| **OptimizeCommand** | Fixed `--dev` flag for all package managers |
| **DatabaseSeedCommand** | Exception logging now works correctly |

---

### Breaking Changes

None! This is a fully backward-compatible release.

---

### Upgrade

```bash
# With pip
pip install --upgrade fastman

# With uv
uv tool upgrade fastman

# With pipx
pipx upgrade fastman
```

---

### Contributors

Thanks to everyone who contributed to this release!

---

## Previous Releases

### v0.2.0

- Initial public release
- Project scaffolding with multiple patterns
- Database migrations with Alembic
- Authentication scaffolding (JWT, OAuth, Keycloak)

### v0.1.0

- Internal beta release
