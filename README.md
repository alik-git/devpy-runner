# devpy-runner

`devpy` is a small command for running Python commands through a
git-worktree-local `.venv` overlay backed by a named conda environment.

It is meant for development repos where conda owns the heavy dependency stack
and the worktree-local `.venv` owns editable installs.

## Status

This is an early prototype. Version 1 is intentionally conda-only.

## Install

From this checkout:

```bash
python -m pip install -e ".[dev]"
```

That exposes the command:

```bash
devpy --help
```

## Repo Setup

Add `devpy.toml` at the git root of a repo that should use `devpy`:

```toml
[python]
base_conda_env = "my-conda-env"

[editables]
packages = [
  ".",
]
```

For multiple editable local packages:

```toml
[python]
base_conda_env = "my-conda-env"

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

Add `.venv/` to `.gitignore`.

## Usage

Show the current setup:

```bash
devpy info
```

Create `.venv` if needed and install configured editables:

```bash
devpy update-editables
```

Run normal commands through the worktree `.venv`:

```bash
devpy python script.py
devpy pytest
```

Editable installs are intentionally not managed through ad hoc
`devpy pip install -e ...` commands. Add editable packages to `devpy.toml`, then
run `devpy update-editables`.

Remove the worktree `.venv`:

```bash
devpy clean
```

## Behavior

`devpy` does this:

1. Uses `git rev-parse --show-toplevel` to find the current git worktree root.
2. Requires `devpy.toml` at that root.
3. Creates `.venv` with:

   ```bash
   conda run -n <base_conda_env> --no-capture-output \
     python -m venv --system-site-packages .venv
   ```

4. Runs normal commands with `.venv/bin` first on `PATH`.
5. Sets `PYTHONNOUSERSITE=1`.

By default, `update-editables` uses `pip install --no-deps -e ...` because the
base conda environment is expected to own dependencies. If a repo needs editable
dependencies installed into `.venv`, set:

```toml
[editables]
install_deps = true
packages = ["."]
```

## Unsupported By Design

Version 1 does not support uv-managed environments, non-conda base
environments, or automatic dependency solving. Those can be added later if the
conda-backed overlay workflow proves useful.
