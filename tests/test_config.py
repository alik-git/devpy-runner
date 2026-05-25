"""Tests for devpy config parsing."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from devpy_runner.config import DevpyError, load_config

if TYPE_CHECKING:
    from pathlib import Path


def write_config(root: Path, text: str) -> None:
    """Write a devpy config for a test repo."""
    (root / "devpy.toml").write_text(text, encoding="utf-8")


def test_load_minimal_config(tmp_path: Path) -> None:
    """Load the smallest supported config."""
    write_config(
        tmp_path,
        """
        [python]
        base_conda_env = "example"

        [editables]
        packages = ["."]
        """,
    )

    config = load_config(tmp_path)

    assert config.base_conda_env == "example"
    assert config.venv == tmp_path / ".venv"
    assert config.editable_packages == (tmp_path,)
    assert config.install_editable_deps is False


def test_editables_can_point_to_sibling_worktrees(tmp_path: Path) -> None:
    """Allow editable packages outside the owning git root."""
    write_config(
        tmp_path,
        """
        [python]
        base_conda_env = "example"

        [editables]
        packages = ["../sibling"]
        """,
    )

    config = load_config(tmp_path)

    assert config.editable_packages == ((tmp_path / "../sibling").resolve(),)


def test_editables_can_use_absolute_paths(tmp_path: Path) -> None:
    """Allow editable packages to point at canonical checkouts."""
    package = tmp_path / "repos" / "package"
    write_config(
        tmp_path,
        f"""
        [python]
        base_conda_env = "example"

        [editables]
        packages = [{str(package)!r}]
        """,
    )

    config = load_config(tmp_path)

    assert config.editable_packages == (package,)


def test_editables_can_use_tilde_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Allow editable packages to use user-home anchored paths."""
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    write_config(
        tmp_path,
        """
        [python]
        base_conda_env = "example"

        [editables]
        packages = ["~/repos/package"]
        """,
    )

    config = load_config(tmp_path)

    assert config.editable_packages == (home / "repos" / "package",)


def test_venv_must_stay_inside_git_root(tmp_path: Path) -> None:
    """Reject venv paths outside the current git root."""
    write_config(
        tmp_path,
        """
        [python]
        base_conda_env = "example"
        venv = "../outside"
        """,
    )

    with pytest.raises(DevpyError, match="python.venv must stay inside"):
        load_config(tmp_path)


def test_missing_config_has_clear_error(tmp_path: Path) -> None:
    """Explain how to create the required config."""
    with pytest.raises(DevpyError, match="missing devpy.toml"):
        load_config(tmp_path)
