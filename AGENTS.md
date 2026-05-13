# AGENTS.md

Repo-specific instructions for agents working with `devpy-runner`.

## Package Conventions

- Keep importable package code under `src/devpy_runner/`.
- Keep the console entry point named `devpy`.
- Keep this package agnostic: do not add organization-specific, robotics-specific,
  or machine-specific defaults.
- Version 1 is intentionally conda-only. Do not add uv or other environment
  backends until the conda-backed overlay workflow is proven useful.

## Validation

- For Python or packaging changes, run Ruff, mypy, pytest, and a package build
  check when feasible.
- Keep tests focused on config parsing, command construction, failure messages,
  and the small public command surface.

## Pull Requests

- Use `.github/PULL_REQUEST_TEMPLATE.md` for PR descriptions.
- Do not commit secrets, credentials, local runtime config, or scratch notes.
