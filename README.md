# devpy-runner

Editable Python installs in git worktrees without copying heavy dependencies.

`devpy` runs commands inside a shared conda environment with a
git-worktree-local `.venv` overlay. Use it when conda owns the heavy dependency
stack and each worktree needs its own editable Python installs.

## Why

Git worktrees are useful for working on multiple branches at once, but Python
editable installs make them easy to misuse:

- one shared conda env can accidentally import code from the wrong worktree
- one full conda env per worktree duplicates large dependencies
- `PYTHONPATH` skips normal package metadata and console scripts

`devpy` keeps the split explicit:

- conda env: heavy shared dependencies
- worktree `.venv`: editable local packages and console scripts
- `devpy.toml`: the worktree's configuration

You do not need to `conda activate` the shared environment before running
`devpy` commands. `devpy` reads `devpy.toml`, applies the configured conda
environment to the child process, and keeps the worktree `.venv/bin` first on
`PATH`.

## Status

Version 1 is intentionally conda-only. It does not solve dependency management
for every Python project; it solves the conda-backed worktree overlay workflow.

## Install

From PyPI:

```bash
python -m pip install devpy-runner
```

For development from this checkout:

```bash
python -m pip install -e ".[dev]"
```

Check the command:

```bash
devpy --help
```

## Quick Start

Create a shared conda environment that has your normal dependencies, but not the
editable package you are developing:

```bash
conda create -n myproject-shared python=3.11 pip -y
conda run -n myproject-shared python -m pip install -U pip
```

In a git worktree, add `devpy.toml` at the git root:

```toml
[python]
base_conda_env = "myproject-shared"

[editables]
packages = [
  ".",
]
```

Create the worktree `.venv` and install configured editables:

```bash
devpy update-editables
```

Run commands through the worktree environment:

```bash
devpy python -c "import sys; print(sys.executable)"
devpy pytest
devpy python scripts/example.py
```

These commands do not require `conda activate myproject-shared` first. The
configured conda env still supplies native libraries, activation-script
environment variables, and shared dependencies.

Verify that your editable package is imported from the current worktree:

```bash
devpy python -c "import mypackage; print(mypackage.__file__)"
```

## Worktree-Local Config

If `devpy.toml` is local machine config, ignore it with the git worktree's
exclude file. In git worktrees, `.git` may be a file, so use `git rev-parse`:

```bash
EXCLUDE="$(git rev-parse --git-path info/exclude)"
mkdir -p "$(dirname "$EXCLUDE")"
printf '\n# Local devpy config\n/devpy.toml\n/.venv/\n' >> "$EXCLUDE"
```

If `devpy.toml` should be shared by the team, commit it instead and only ignore
`.venv/`.

## Multiple Editable Packages

One worktree can own an environment for several local packages:

```toml
[python]
base_conda_env = "myproject-shared"

[editables]
packages = [
  ".",
  "../some-sibling-package",
  "../another-sibling-package",
]
```

Editable paths are resolved relative to the git root. They may point to sibling
checkouts. The `.venv` path defaults to `.venv` and must stay inside the git
root.

## Commands

Show configuration without creating `.venv`:

```bash
devpy info
```

Create `.venv` if needed and install configured editables:

```bash
devpy update-editables
```

Run normal commands inside the configured conda env, with `.venv/bin` first on
`PATH`:

```bash
devpy python -m pytest
devpy pytest
devpy my-console-script --help
```

Remove the worktree `.venv`:

```bash
devpy clean
```

## Editable Installs

Editable installs are configured in `devpy.toml`, not through ad hoc pip
commands.

These intentionally fail:

```bash
devpy pip install -e .
devpy pip install --editable ../some-package
devpy python -m pip install -e .
```

Use this instead:

```toml
[editables]
packages = [
  ".",
  "../some-package",
]
```

```bash
devpy update-editables
```

By default, `update-editables` uses `pip install --no-deps -e ...` because the
base conda environment is expected to own dependencies. If a repo really needs
editable dependencies installed into `.venv`, set:

```toml
[editables]
install_deps = true
packages = ["."]
```

## Config Reference

```toml
[python]
base_conda_env = "myproject-shared"
venv = ".venv"

[editables]
packages = ["."]
install_deps = false
```

Fields:

- `python.base_conda_env`: required conda environment name.
- `python.venv`: optional worktree-local virtual environment path. Defaults to
  `.venv`.
- `editables.packages`: editable package paths, relative to the git root.
- `editables.install_deps`: whether pip should install dependencies while
  installing editables. Defaults to `false`.

## Troubleshooting

If `devpy` is not found, install it in the active Python environment:

```bash
python -m pip install --upgrade devpy-runner
```

If `devpy` says `missing devpy.toml`, make sure you are inside a git worktree
and that `devpy.toml` exists at the git root:

```bash
git rev-parse --show-toplevel
```

If imports come from the wrong place, check the active paths:

```bash
devpy info
devpy python -c "import mypackage; print(mypackage.__file__)"
```

If `.venv` gets stale, remove and recreate it:

```bash
devpy clean
devpy update-editables
```

## Unsupported By Design

Version 1 does not support uv-managed environments, non-conda base
environments, or automatic dependency solving. Those can be added later if the
conda-backed overlay workflow proves useful.
