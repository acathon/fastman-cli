---
sidebar_position: 1
---

# Installation

Get Fastman up and running in under a minute.

## Requirements

- **Python 3.9 or higher** — check with `python --version`
- **A package manager** — pip, uv, poetry, or pipenv (pip comes with Python)

## Installation Methods

### Using pip

The simplest way to install:

```bash
pip install fastman
```

This installs Fastman along with its core dependencies (`rich` for styled terminal output and `pyfiglet` for ASCII banners).

### Using uv (Recommended for speed)

[uv](https://github.com/astral-sh/uv) is an extremely fast Python package manager written in Rust. If you want the fastest install experience:

```bash
uv tool install fastman
```

### Using pipx

For a globally isolated install that won't conflict with other Python packages:

```bash
pipx install fastman
```

## Verify Installation

After installing, verify everything works:

```bash
fastman --version
```

You should see output like:

```
Fastman v0.3.3 (Cheetah)
Python 3.12.0
Package Manager: uv
```

:::tip Troubleshooting
If `fastman` is not recognized, make sure your Python scripts directory is on your system PATH. For pip installs, this is typically `~/.local/bin` (Linux/macOS) or `%APPDATA%\Python\Scripts` (Windows).
:::

## Included Tooling

Fastman installs its CLI dependencies automatically, including Rich, Pyfiglet, IPython, and certifi.

- `ipython` powers `fastman tinker` out of the box
- `certifi` provides the CA bundle used by `fastman install:certificate`

## Updating Fastman

```bash
# With pip
pip install --upgrade fastman

# With uv
uv tool upgrade fastman

# With pipx
pipx upgrade fastman
```

## Next Steps

Now that Fastman is installed, create your first project:

```bash
fastman new my-api
```

Continue to [Creating Your First Project →](./getting-started/first-project)
