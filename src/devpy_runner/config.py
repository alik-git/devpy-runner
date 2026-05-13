"""Configuration loading for devpy."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class DevpyError(Exception):
    """User-facing devpy error."""


@dataclass(frozen=True)
class DevpyConfig:
    """Parsed devpy configuration."""

    root: Path
    base_conda_env: str
    venv: Path
    editable_packages: tuple[Path, ...]
    install_editable_deps: bool


def load_config(root: Path) -> DevpyConfig:
    """Load and validate ``devpy.toml`` from a git worktree root."""
    config_path = root / "devpy.toml"
    if not config_path.is_file():
        raise DevpyError(
            "missing devpy.toml at git root:\n"
            f"  {config_path}\n\n"
            "Create devpy.toml with:\n\n"
            "[python]\n"
            'base_conda_env = "your-conda-env"\n\n'
            "[editables]\n"
            'packages = ["."]',
        )

    try:
        with config_path.open("rb") as file:
            raw = tomllib.load(file)
    except tomllib.TOMLDecodeError as exc:
        raise DevpyError(f"invalid devpy.toml: {exc}") from exc

    if not isinstance(raw, dict):
        raise DevpyError("devpy.toml must contain TOML tables")

    python = _table(raw, "python")
    base_conda_env = _required_nonempty_string(python, "base_conda_env")
    venv_value = _optional_nonempty_string(python, "venv", default=".venv")
    venv = _resolve_repo_path(root, venv_value, field="python.venv")

    editables = _table(raw, "editables", required=False)
    editable_values = _optional_string_list(editables, "packages")
    install_deps = _optional_bool(editables, "install_deps", default=False)

    editable_packages = tuple(
        _resolve_path(root, value, field="editables.packages")
        for value in editable_values
    )

    return DevpyConfig(
        root=root,
        base_conda_env=base_conda_env,
        venv=venv,
        editable_packages=editable_packages,
        install_editable_deps=install_deps,
    )


def _table(raw: dict[str, Any], key: str, *, required: bool = True) -> dict[str, Any]:
    value = raw.get(key)
    if value is None:
        if required:
            raise DevpyError(f"devpy.toml missing [{key}] table")
        return {}
    if not isinstance(value, dict):
        raise DevpyError(f"devpy.toml [{key}] must be a table")
    return value


def _required_nonempty_string(raw: dict[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise DevpyError(f"devpy.toml requires non-empty string: {key}")
    return value.strip()


def _optional_nonempty_string(
    raw: dict[str, Any],
    key: str,
    *,
    default: str,
) -> str:
    value = raw.get(key, default)
    if not isinstance(value, str) or not value.strip():
        raise DevpyError(f"devpy.toml field must be a non-empty string: {key}")
    return value.strip()


def _optional_string_list(raw: dict[str, Any], key: str) -> tuple[str, ...]:
    value = raw.get(key, [])
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise DevpyError(f"devpy.toml field must be a list of strings: {key}")
    return tuple(item for item in value if item.strip())


def _optional_bool(raw: dict[str, Any], key: str, *, default: bool) -> bool:
    value = raw.get(key, default)
    if not isinstance(value, bool):
        raise DevpyError(f"devpy.toml field must be a boolean: {key}")
    return value


def _resolve_repo_path(root: Path, value: str, *, field: str) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        raise DevpyError(f"devpy.toml {field} must be relative to the git root")
    resolved = (root / path).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise DevpyError(f"devpy.toml {field} must stay inside the git root") from exc
    return resolved


def _resolve_path(root: Path, value: str, *, field: str) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        raise DevpyError(f"devpy.toml {field} must be relative to the git root")
    return (root / path).resolve()
