---
sidebar_position: 2
---

# Installation

Getting started with Fastman is simple. You can install it globally or use it as a script.

## Prerequisites

- Python 3.8+
- pip (or uv/poetry)

## Installation Methods

### Option 1: Global Installation (Recommended)

If `fastman-cli` is published to PyPI (coming soon), you can install it via pip:

```bash
pip install fastman-cli
```

### Option 2: Manual Setup

1.  Clone the repository or download the `cli.py` script.
2.  Make it executable and move it to your path.

```bash
# Rename to fastman and make executable
mv cli.py fastman
chmod +x fastman

# Move to a bin directory (optional)
sudo mv fastman /usr/local/bin/
```

## Verification

Verify the installation by running:

```bash
fastman --version
```

You should see the current version of Fastman CLI.
