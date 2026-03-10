# Contributing to Fastman

First off, thank you for considering contributing to Fastman! It's people like you that make Fastman such a great tool.

Following these guidelines helps to communicate that you respect the time of the developers managing and developing this open source project. In return, they should reciprocate that respect in addressing your issue, assessing changes, and helping you finalize your pull requests.

## Code of Conduct

By participating in this project, you are expected to uphold our [Code of Conduct](CODE_OF_CONDUCT.md).

## Getting Started

### Prerequisites

* Python 3.9 or higher
* `uv` (recommended), `poetry`, `pipenv`, or `pip`
* Git

### Local Development Setup

1. Fork the repository and clone it locally:
    ```bash
    git clone https://github.com/YOUR_USERNAME/fastman-cli.git
    cd fastman-cli
    ```

2. Add the upstream remote:
    ```bash
    git remote add upstream https://github.com/acathon/fastman-cli.git
    ```

3. Set up the development environment. We recommend using `uv`, but you can also use `pip`:
    ```bash
    # Using uv (recommended)
    uv pip install -e ".[dev]"

    # Or using pip
    pip install -e ".[dev]"
    ```

## Development Workflow

1. Always branch off from the `main` branch:
    ```bash
    git checkout main
    git pull upstream main
    git checkout -b feature/your-feature-name
    ```
   *For bugs, you might use `bugfix/issue-description` instead.*

2. Make your changes in the `src/` directory. Fastman uses a `src` layout.

3. Run the tests. Because of the `src` layout, you need to set the `PYTHONPATH`:
    ```bash
    PYTHONPATH=src pytest
    ```
    Ensure all tests pass before submitting your code.

4. Format and lint your code:
    ```bash
    black src/ tests/
    isort src/ tests/
    ```

## Submitting Changes

1. Commit your changes. Write clear, descriptive commit messages.
    ```bash
    git add .
    git commit -m "feat: Add support for custom templates"
    ```

2. Push your branch to your fork:
    ```bash
    git push origin feature/your-feature-name
    ```

3. Open a Pull Request against the `main` branch of the upstream repository.
   * Ensure the PR description clearly describes the problem and solution.
   * Reference any related issues.

## Reporting Issues

* Use the GitHub Issue Tracker to report bugs or request features.
* Check if the issue has already been reported before creating a new one.
* When reporting a bug, provide detailed steps to reproduce, including your OS, Python version, and Fastman version.

## Architecture & Code Guidelines

* Fastman commands are located in `src/fastman/commands/`.
* Utilities are in `src/fastman/utils.py`.
* **Important:** When generating templates, ensure you use SQLAlchemy's single-query `delete()` method for performance (e.g., `db.query(Model).filter(...).delete()`).
* **Important:** Avoid global mocking of `pathlib.Path` methods in tests. Use scoped patching. When testing functions accepting `pathlib.Path` objects, use `MagicMock(spec=Path)`.
* **Important:** When modifying Fastman CLI commands or Alembic environments that manipulate `sys.path`, always use `sys.path.append()` rather than `sys.path.insert(0, ...)` to prevent local files from shadowing standard library modules.
* **Important:** Commands that execute subprocesses must handle errors properly using `check=True` or `try/except`.

Thank you for contributing!
