"""Per-user XDG store resolution for kanban-tui.

User scope is the XDG config/data pair the rest of the app already uses.
Resolution is fail-closed: never fall back to cwd or another scope.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from xdg_base_dirs import xdg_config_home, xdg_data_home

from kanban_tui.constants import CONFIG_NAME, DATABASE_NAME

SCOPE_USER = "user"
IMPLEMENTED_SCOPES = (SCOPE_USER,)


class ScopeError(Exception):
    """User-scope roots cannot be resolved or used."""


@dataclass(frozen=True)
class UserScope:
    config_dir: Path
    config_file: Path
    data_dir: Path
    database_file: Path


def _require_home() -> Path:
    try:
        home = Path.home()
    except RuntimeError as e:
        raise ScopeError(
            "user scope cannot be resolved: home directory is not set"
        ) from e
    if not home.exists():
        raise ScopeError("user scope cannot be resolved: home directory does not exist")
    if not os.access(home, os.R_OK):
        raise ScopeError("user scope cannot be resolved: home directory is unreadable")
    return home


def _xdg_root(getter, label: str) -> Path:
    try:
        return getter()
    except RuntimeError as e:
        raise ScopeError(
            f"user scope cannot be resolved: {label} directory is unavailable"
        ) from e


def _check_tree(path: Path, label: str) -> None:
    if path.exists():
        if not path.is_dir():
            raise ScopeError(f"cannot read user-scope {label}: not a directory")
        if not os.access(path, os.R_OK | os.X_OK):
            raise ScopeError(f"cannot read user-scope {label}")
        if not os.access(path, os.W_OK):
            raise ScopeError(f"cannot write user-scope {label}")
        return

    ancestor = path.parent
    while not ancestor.exists() and ancestor != ancestor.parent:
        ancestor = ancestor.parent
    if not ancestor.exists():
        raise ScopeError(f"cannot write user-scope {label}: parent is missing")
    if not os.access(ancestor, os.W_OK | os.X_OK):
        raise ScopeError(f"cannot write user-scope {label}")


def resolve_user_scope() -> UserScope:
    """Resolve per-user config and data roots via XDG.

    Does not create directories. Raises ScopeError instead of using cwd
    or any non-user store.
    """
    _require_home()
    config_root = _xdg_root(xdg_config_home, "config")
    data_root = _xdg_root(xdg_data_home, "data")

    config_dir = config_root / "kanban_tui"
    data_dir = data_root / "kanban_tui"
    _check_tree(config_dir, "config")
    _check_tree(data_dir, "data")

    return UserScope(
        config_dir=config_dir,
        config_file=config_dir / CONFIG_NAME,
        data_dir=data_dir,
        database_file=data_dir / DATABASE_NAME,
    )


def ensure_user_scope_dirs(scope: UserScope) -> None:
    scope.config_dir.mkdir(exist_ok=True, parents=True)
    scope.data_dir.mkdir(exist_ok=True, parents=True)


def bind_user_scope_env(scope: UserScope) -> None:
    """Point process env at the resolved user store so CLI subprocesses match."""
    os.environ["KANBAN_TUI_CONFIG_FILE"] = scope.config_file.as_posix()
    os.environ["KANBAN_TUI_DATABASE_FILE"] = scope.database_file.as_posix()
