import os
from pathlib import Path

from kanban_tui.backends.jira.backend import JiraBackend
from kanban_tui.config import Settings


def test_init_backend(test_jira_config: Settings, test_auth_path):
    os.environ["KANBAN_TUI_AUTH_FILE"] = test_auth_path
    backend = JiraBackend(settings=test_jira_config.backend.jira_settings)
    assert backend.settings.base_url == "http://localhost:8080"
    assert backend.settings.auth_file_path == test_auth_path
    assert Path(test_auth_path).exists()
