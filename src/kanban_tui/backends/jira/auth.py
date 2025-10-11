from pathlib import Path

from kanban_tui.constants import AUTH_FILE


def check_auth_file_exists(file: str = AUTH_FILE.as_posix()) -> bool:
    return Path(file).exists()


def init_auth_file(file: str = AUTH_FILE.as_posix()) -> None:
    if not check_auth_file_exists(file):
        Path(file).touch()


def read_api_key(): ...
