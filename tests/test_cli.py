"""Tests for devpy command behavior."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING
from unittest.mock import ANY

import pytest

from devpy_runner.cli import (
    clean,
    conda_run_command,
    devpy_env,
    ensure_venv,
    find_git_root,
    reject_editable_pip_install,
    run_passthrough,
    update_editables,
)
from devpy_runner.config import DevpyConfig, DevpyError

if TYPE_CHECKING:
    from pathlib import Path


def config(root: Path, *, editables: tuple[Path, ...] = ()) -> DevpyConfig:
    """Build a test config."""
    return DevpyConfig(
        root=root,
        base_conda_env="base-env",
        venv=root / ".venv",
        editable_packages=editables,
        install_editable_deps=False,
    )


def test_find_git_root_uses_git_command(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Find the git root through git rather than directory scanning."""

    def fake_run(
        args: list[str],
        **kwargs: object,
    ) -> subprocess.CompletedProcess[str]:
        assert args == ["git", "rev-parse", "--show-toplevel"]
        assert kwargs["cwd"] == tmp_path
        return subprocess.CompletedProcess(args, 0, stdout=f"{tmp_path}\n", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert find_git_root(tmp_path) == tmp_path.resolve()


def test_find_git_root_fails_clearly(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fail quickly outside git worktrees."""

    def fake_run(
        args: list[str],
        **_kwargs: object,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args, 128, stdout="", stderr="no git")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(DevpyError, match="not inside a git worktree"):
        find_git_root(tmp_path)


def test_ensure_venv_creates_overlay_with_conda(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Create a system-site-packages venv from the configured conda env."""
    calls: list[list[str]] = []
    monkeypatch.setenv("CONDA_EXE", "/opt/conda/bin/conda")

    def fake_run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        assert kwargs["cwd"] == tmp_path
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    ensure_venv(config(tmp_path))

    assert calls == [
        [
            "/opt/conda/bin/conda",
            "run",
            "-n",
            "base-env",
            "--no-capture-output",
            "python",
            "-m",
            "venv",
            "--system-site-packages",
            str(tmp_path / ".venv"),
        ],
    ]


def test_update_editables_installs_no_deps_by_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Install configured editable packages with no dependency solving."""
    package = tmp_path / "package"
    package.mkdir()
    calls: list[list[str]] = []
    monkeypatch.setenv("CONDA_EXE", "/opt/conda/bin/conda")

    def fake_run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        assert kwargs["cwd"] == tmp_path
        assert kwargs["env"]["PATH"].split(":")[0] == str(tmp_path / ".venv" / "bin")
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    update_editables(config(tmp_path, editables=(package,)))

    assert calls == [
        [
            "/opt/conda/bin/conda",
            "run",
            "-n",
            "base-env",
            "--no-capture-output",
            "--",
            "python",
            "-c",
            ANY,
            str(tmp_path / ".venv" / "bin"),
            str(tmp_path / ".venv" / "bin" / "python"),
            "-m",
            "pip",
            "install",
            "--no-deps",
            "-e",
            str(package),
        ],
    ]


def test_passthrough_runs_inside_conda_with_venv_first(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Run normal commands with conda activation and the worktree overlay."""
    calls: list[list[str]] = []
    monkeypatch.setenv("CONDA_EXE", "/opt/conda/bin/conda")

    def fake_run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        assert kwargs["cwd"] == tmp_path
        assert kwargs["env"]["PATH"].split(":")[0] == str(tmp_path / ".venv" / "bin")
        return subprocess.CompletedProcess(args, 7)

    monkeypatch.setattr(subprocess, "run", fake_run)

    returncode = run_passthrough(config(tmp_path), ["pytest", "-q"])

    assert returncode == 7
    assert calls == [
        [
            "/opt/conda/bin/conda",
            "run",
            "-n",
            "base-env",
            "--no-capture-output",
            "--",
            "python",
            "-c",
            ANY,
            str(tmp_path / ".venv" / "bin"),
            "pytest",
            "-q",
        ],
    ]


def test_conda_run_command_separates_conda_args(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Separate conda options from the command being run."""
    monkeypatch.setenv("CONDA_EXE", "/opt/conda/bin/conda")

    assert conda_run_command(config(tmp_path), ["python", "--version"]) == [
        "/opt/conda/bin/conda",
        "run",
        "-n",
        "base-env",
        "--no-capture-output",
        "--",
        "python",
        "-c",
        ANY,
        str(tmp_path / ".venv" / "bin"),
        "python",
        "--version",
    ]


def test_clean_removes_venv(tmp_path: Path) -> None:
    """Remove the configured worktree venv."""
    venv = tmp_path / ".venv"
    venv.mkdir()

    clean(config(tmp_path))

    assert not venv.exists()


def test_devpy_env_prefers_venv_bin(tmp_path: Path) -> None:
    """Put the worktree venv first on PATH."""
    env = devpy_env(config(tmp_path))

    assert env["PATH"].split(":")[0] == str(tmp_path / ".venv" / "bin")
    assert env["PYTHONNOUSERSITE"] == "1"


@pytest.mark.parametrize(
    "args",
    [
        ["pip", "install", "-e", "."],
        ["pip", "install", "--editable", "."],
        ["python", "-m", "pip", "install", "-e", "."],
        ["python", "-m", "pip", "install", "--editable", "."],
    ],
)
def test_reject_editable_pip_install(args: list[str]) -> None:
    """Reject editable installs outside devpy.toml."""
    with pytest.raises(DevpyError, match="devpy update-editables"):
        reject_editable_pip_install(args)


@pytest.mark.parametrize(
    "args",
    [
        ["pip", "install", "requests"],
        ["python", "-m", "pip", "install", "requests"],
        ["pytest"],
    ],
)
def test_allow_non_editable_passthrough_commands(args: list[str]) -> None:
    """Allow ordinary passthrough commands."""
    reject_editable_pip_install(args)
