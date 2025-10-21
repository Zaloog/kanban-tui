import os
from pathlib import Path

from kanban_tui.backends.auth import AuthSettings, init_auth_file


def test_init_auth_dir(test_auth_path) -> None:
    os.environ["KANBAN_TUI_AUTH_FILE"] = test_auth_path
    assert not Path(test_auth_path).exists()
    assert init_auth_file(test_auth_path) == "Auth file created"
    assert Path(test_auth_path).exists()


def test_read_api_key_from_empty():
    # Give different file to look for
    os.environ["KANBAN_TUI_AUTH_FILE"] = (
        Path(__file__).parent.parent / "sample-configs/not_existent_file.toml"
    ).as_posix()
    auth = AuthSettings()

    assert auth.jira.api_key == ""


def test_read_api_key(test_auth_file):
    auth = AuthSettings()
    assert auth.jira.api_key == "MY_TEST_KEY"


def test_update_api_key(test_auth_path):
    os.environ["KANBAN_TUI_AUTH_FILE"] = test_auth_path
    auth = AuthSettings()
    assert auth.jira.api_key == ""
    # Update Key in temp File
    auth.set_jira_api_key(new_api_key="ANOTHER_KEY")
    # Read again
    auth = AuthSettings()
    assert auth.jira.api_key == "ANOTHER_KEY"


def test_update_cert_path(test_auth_path):
    os.environ["KANBAN_TUI_AUTH_FILE"] = test_auth_path
    auth = AuthSettings()
    assert auth.jira.cert_path == ""
    # Update Key in temp File
    auth.set_cert_path(new_cert_path="NEW_PATH")
    # Read again
    auth = AuthSettings()
    assert auth.jira.cert_path == "NEW_PATH"


def test_default_auth(test_auth_path):
    os.environ["KANBAN_TUI_AUTH_FILE"] = test_auth_path
    auth = AuthSettings()
    auth_dict = auth.model_dump(serialize_as_any=True)
    default_auth = {
        "jira": {
            "api_key": "",
            "cert_path": "",
        }
    }
    assert auth_dict == default_auth
