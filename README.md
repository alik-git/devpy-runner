# Python Package Template

A minimal template for building a modern Python package.

This template includes a standard `src/` package layout, Ruff formatting and
linting, mypy type checking, pytest, pre-commit hygiene checks, GitHub Actions
CI, and package build checks for both pip and uv workflows.

## Template Setup

1. Pick a package name.

   Use a short lowercase import name like `numpy` or `pandas`. The import
   package name is usually underscore-separated, while the PyPI/project name may
   use hyphens.

2. Rename the package folder:

   ```bash
   mv src/mypackage src/your_package_name
   ```

3. Replace `mypackage` with your package name in:

   - `name`
   - `[project.urls]`
   - `[project.scripts]`
   - Ruff `known-first-party`
   - mypy `files`
   - `tests/test_package.py`
   - `AGENTS.md`
   - this README

   Most of these are in [`pyproject.toml`](pyproject.toml).

4. Fill in basic package metadata in [`pyproject.toml`](pyproject.toml):

   - `description`
   - `authors`
   - `maintainers`
   - `keywords`
   - `classifiers`

5. Add a license if the package will be public or open source. The files under
   [`templates/licenses`](templates/licenses) are templates only and do not
   license this repository.

   ```bash
   cp templates/licenses/MIT LICENSE
   ```

   or:

   ```bash
   cp templates/licenses/Apache-2.0 LICENSE
   ```

   Then replace the copyright placeholder and add the matching `license` value
   in `pyproject.toml`, either `MIT` or `Apache-2.0`.

   After choosing a license, the templates can be removed.

6. Add your code under `src/your_package_name/` and, if needed, expose a public
   API from `src/your_package_name/__init__.py`.

7. Update this README as needed for the package you are building.

## Installation

Recommended with `uv`:

```bash
uv sync --extra dev
```

This repository commits `.python-version` and `uv.lock` so the uv workflow uses
Python 3.11 by default and resolves reproducible dependency versions. After
changing package metadata or dependencies, update the lockfile with:

```bash
uv lock
```

Standard Python fallback:

```bash
python -m pip install -e ".[dev]"
```

Conda can still own the outer environment if needed:

```bash
conda create -n mypackage python=3.11
conda activate mypackage
python -m pip install -e ".[dev]"
```

## Getting Started

Run the starter Python API:

```python
import mypackage

result = mypackage.do_useful_thing("world")
```

Run the starter CLI:

```bash
mypackage
```

## Development Workflow

Run the standard checks before opening a PR:

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest
uv run pre-commit run --all-files
uv build
```

If you are using standard Python tools instead of uv:

```bash
python -m ruff format --check .
python -m ruff check .
python -m mypy
python -m pytest
python -m pre_commit run --all-files
python -m build
```

Pre-commit hooks are optional. To enable local checks before each commit:

```bash
uv run pre-commit install
```

## Project Layout

```text
src/mypackage/
  __init__.py   # public import surface
  package.py    # reusable package logic
  cli.py        # command-line boundary
  py.typed      # marker for typed packages

tests/
  test_package.py
```

## CI / GitHub Actions

GitHub Actions runs:

- fast Ruff-only checks
- Ruff, mypy, pre-commit hygiene, and pytest
- package build and wheel smoke test with pip
- package build and wheel smoke test with uv

Local pre-commit hooks are not installed automatically. Running
`pre-commit install` is optional.

## Documentation

Project documentation lives in [`docs/`](docs/):

- [`docs/api.md`](docs/api.md): public API notes and examples
- [`docs/ci-private-submodules.md`](docs/ci-private-submodules.md): GitHub
  Actions setup for private submodules

## Troubleshooting

Add project-specific troubleshooting notes here when setup or runtime issues
come up repeatedly.
