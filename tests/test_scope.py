import os
from pathlib import Path

import pytest

from kanban_tui.scope import (
    ScopeError,
    bind_user_scope_env,
    ensure_user_scope_dirs,
    resolve_user_scope,
)


def _point_home(monkeypatch, home: Path) -> None:
    home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    monkeypatch.setenv("XDG_DATA_HOME", str(home / ".local" / "share"))
    monkeypatch.delenv("KANBAN_TUI_CONFIG_FILE", raising=False)
    monkeypatch.delenv("KANBAN_TUI_DATABASE_FILE", raising=False)


def test_resolve_user_scope_uses_xdg(tmp_path, monkeypatch):
    home = tmp_path / "home"
    _point_home(monkeypatch, home)

    scope = resolve_user_scope()

    assert scope.config_dir == home / ".config" / "kanban_tui"
    assert (
        scope.database_file
        == home / ".local" / "share" / "kanban_tui" / "kanban_tui.db"
    )
    assert not scope.config_dir.exists()
    assert not scope.data_dir.exists()


def test_resolve_user_scope_missing_home(monkeypatch):
    def no_home():
        raise RuntimeError("HOME is not set")

    monkeypatch.setattr("kanban_tui.scope.Path.home", staticmethod(no_home))

    with pytest.raises(ScopeError, match="home directory is not set"):
        resolve_user_scope()


def test_resolve_user_scope_unreadable_home(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr("kanban_tui.scope.Path.home", staticmethod(lambda: home))
    monkeypatch.setattr(
        "kanban_tui.scope.os.access",
        lambda path, mode, *args, **kwargs: Path(path) != home,
    )

    with pytest.raises(ScopeError, match="home directory is unreadable"):
        resolve_user_scope()


def test_bind_user_scope_env_overwrites_project_override(tmp_path, monkeypatch):
    home = tmp_path / "home"
    _point_home(monkeypatch, home)
    monkeypatch.setenv(
        "KANBAN_TUI_CONFIG_FILE", str(tmp_path / "project" / "config.toml")
    )
    monkeypatch.setenv(
        "KANBAN_TUI_DATABASE_FILE", str(tmp_path / "project" / "kanban_tui.db")
    )

    scope = resolve_user_scope()
    ensure_user_scope_dirs(scope)
    bind_user_scope_env(scope)

    assert os.environ["KANBAN_TUI_CONFIG_FILE"] == scope.config_file.as_posix()
    assert os.environ["KANBAN_TUI_DATABASE_FILE"] == scope.database_file.as_posix()
    assert not (tmp_path / "project" / "kanban_tui.db").exists()
