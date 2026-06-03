# devpy-runner

> Deprecated: `devpy-runner` has moved to
> [`notuv`](https://github.com/alik-git/notuv). Install and use `notuv` for new
> work:
>
> ```bash
> python -m pip install --upgrade notuv
> notuv <same arguments>
> ```
>
> This package remains available temporarily for old branches, old VM images,
> and worksets that still use `devpy`, `devpy.toml`, `[devpy]`,
> `devpy.*.toml`, or `.devpy`.

Editable Python installs in git worktrees without copying heavy dependencies.

`devpy` runs commands inside a shared conda environment with a
git-worktree-local `.venv` overlay. Use it when conda owns the heavy dependency
stack and each worktree needs its own editable Python installs.

## Why

If you have ever used Git worktrees for deep learning, you might be familiar with the following problem:

You are working on your project as an editable package installed locally,
you have a conda env with big heavy packages like pytorch and cuda, and then you make a new git worktree to work on a feature in parallel. 

You run your code and it does not behave as expected, because the editable python package was still pointing to your original repo, not the new worktree. Ouch.

So now you either have install the worktree as an editable package, which breaks your original repo!

Or you can set PYTHONPATH= each time you run a command! Ew!

Or you can just set up a new conda env to stay sane, but then after 3 worktrees you have 25GB of conda envs on your machine!


`devpy` solves this specific problem:

- one shared conda env owns the heavy dependency stack
- each worktree gets a tiny `.venv` overlay for its editable installs
- `devpy.toml` says which conda env and editable packages belong to that
  worktree
- `devpy <command>` runs inside the conda env, then puts the worktree `.venv`
  first

`devpy` keeps the split explicit:

- conda env: heavy shared dependencies
- worktree `.venv`: editable local packages and console scripts
- `devpy.toml`: the worktree's configuration

You do not need to `conda activate` the shared environment before running
`devpy` commands. `devpy` reads `devpy.toml`, applies the configured conda
environment to the child process, and keeps the worktree `.venv/bin` first on
`PATH`.

## Install

For new work, install `notuv` instead:

```bash
python -m pip install --upgrade notuv
```

For old branches or VM images that still require `devpy`, install this legacy
package from PyPI:

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

Create one shared conda environment that has your normal dependencies, but not
the editable package you are developing:

```bash
conda create -n myproject-shared python=3.11 pip -y
conda run -n myproject-shared python -m pip install -U pip
```

For a real project, this is where you install PyTorch, CUDA-related packages,
MuJoCo, Isaac Sim, or whatever heavy dependencies the project needs.

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
  "~/Projects/repos/some-canonical-package",
  "../another-sibling-package",
]
```

Relative editable paths are resolved from the git root. Editable paths may also
use absolute paths or `~`, which is useful for canonical shared checkouts such
as `~/Projects/repos/IsaacLab`. The `.venv` path defaults to `.venv` and must
stay inside the git root.

## Explicit Stack Configs

Several repos can share one dependency stack when they belong to the same local
development context. Keep that relationship explicit with a small repo-local
pointer config:

```text
worksets/my-feature/
  devpy.backend.toml
  .devpy/backend/.venv

  api-service/
    devpy.toml

  worker-service/
    devpy.toml
```

The shared stack config owns the base conda env, venv, and editable packages:

```toml
# worksets/my-feature/devpy.backend.toml
[devpy]
kind = "stack"

[python]
base_conda_env = "backend-shared"
venv = ".devpy/backend/.venv"

[editables]
packages = [
  "api-service",
  "worker-service",
  "~/Projects/repos/shared-library",
]
```

Each repo opts into that stack explicitly:

```toml
# worksets/my-feature/api-service/devpy.toml
[devpy]
extends = "../devpy.backend.toml"
```

Run commands from the repo you are working in:

```bash
cd worksets/my-feature/api-service
devpy info
devpy update-editables
devpy pytest
```

Commands run from the active repo root, while relative paths in the stack config
resolve from the stack config directory. A workset can have more than one stack
config when repos need different base conda environments.

Stack venvs may be shared by several repos. `devpy clean` refuses to remove a
shared stack venv unless you say so explicitly:

```bash
devpy clean --shared
```

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

Remove a shared stack `.venv`:

```bash
devpy clean --shared
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

Repo-local config:

```toml
[python]
base_conda_env = "myproject-shared"
venv = ".venv"

[editables]
packages = ["."]
install_deps = false
```

Pointer config:

```toml
[devpy]
extends = "../devpy.backend.toml"
```

Stack config:

```toml
[devpy]
kind = "stack"

[python]
base_conda_env = "backend-shared"
venv = ".devpy/backend/.venv"

[editables]
packages = ["api-service", "worker-service"]
install_deps = false
```

Fields:

- `devpy.extends`: optional path from a repo-local pointer config to one stack
  config.
- `devpy.kind`: set to `"stack"` in stack configs.
- `python.base_conda_env`: required conda environment name.
- `python.venv`: optional virtual environment path. Defaults to `.venv`. In
  repo configs, it must stay inside the repo root. In stack configs, it must
  stay inside the stack config directory. Absolute paths are accepted only when
  they remain inside the allowed root.
- `editables.packages`: editable package paths. Relative paths resolve from the
  config file that declares them. Absolute paths and `~` are also accepted.
- `editables.install_deps`: whether pip should install dependencies while
  installing editables. Defaults to `false`.

## Troubleshooting

If `devpy` is not found, install it in the active Python environment:

```bash
python -m pip install --upgrade devpy-runner
```

For new work, install and run `notuv` instead:

```bash
python -m pip install --upgrade notuv
notuv <same arguments>
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
