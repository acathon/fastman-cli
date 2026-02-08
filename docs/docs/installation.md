---
sidebar_position: 1
---

# Installation

Get Fastman up and running in under a minute.

## Requirements

- Python 3.9 or higher
- pip, uv, poetry, or pipenv

## Installation Methods

### Using uv (Recommended)

[uv](https://github.com/astral-sh/uv) is the fastest Python package manager. Install Fastman as a global tool:

```bash
uv tool install fastman
```

### Using pip

```bash
pip install fastman
```

### Using pipx

For isolated global installs:

```bash
pipx install fastman
```

## Verify Installation

```bash
fastman --version
```

You should see output like:

```
Fastman v0.3.0
Python 3.12.0
Package Manager: uv
```

## Optional Dependencies

Fastman works out of the box, but you can enhance the experience:

```bash
# Rich terminal output (colors, tables, progress bars)
pip install rich

# ASCII art banners
pip install pyfiglet

# Interactive shell enhancements
pip install ipython
```

## Updating Fastman

```bash
# With uv
uv tool upgrade fastman

# With pip
pip install --upgrade fastman
```

## Next Steps

Now that Fastman is installed, create your first project:

```bash
fastman new my-api
```

Continue to [Creating Your First Project →](./getting-started/first-project)
