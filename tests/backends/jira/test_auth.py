from pathlib import Path

from kanban_tui.backends.jira.auth import init_auth_file


def test_init_auth_dir(test_auth_path) -> None:
    init_auth_file(test_auth_path)

    assert Path(test_auth_path).exists()
