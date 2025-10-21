import os
from pathlib import Path

from kanban_tui.app import KanbanTui
from textual.widgets import Input

from kanban_tui.config import Backends
from kanban_tui.modal.modal_auth_screen import ApiKeyWidget, IconButton, ModalAuthScreen

APP_SIZE = (150, 50)


async def test_app_auth_focus_input(test_app: KanbanTui):
    config_path = (
        Path(__file__).parent.parent.parent / "sample-configs/sample_auth.toml"
    )
    os.environ["KANBAN_TUI_AUTH_FILE"] = config_path.as_posix()

    test_app.auth_only = True
    test_app.config.backend.mode = Backends.JIRA
    test_app.backend = test_app.get_backend()
    async with test_app.run_test(size=APP_SIZE) as pilot:
        assert pilot.app.auth_only
        assert isinstance(pilot.app.screen, ModalAuthScreen)
        assert pilot.app.screen.api_key == "MY_TEST_KEY"
        assert isinstance(pilot.app.focused, ApiKeyWidget)


async def test_app_auth_edit(test_app: KanbanTui):
    config_path = (
        Path(__file__).parent.parent.parent / "sample-configs/sample_auth.toml"
    )
    os.environ["KANBAN_TUI_AUTH_FILE"] = config_path.as_posix()

    test_app.auth_only = True
    test_app.config.backend.mode = Backends.JIRA
    test_app.backend = test_app.get_backend()
    async with test_app.run_test(size=APP_SIZE) as pilot:
        assert pilot.app.auth_only
        assert isinstance(pilot.app.screen, ModalAuthScreen)
        assert pilot.app.screen.api_key == "MY_TEST_KEY"
        await pilot.press("e")
        assert isinstance(pilot.app.focused, Input)


async def test_app_auth_save_new_key(test_app: KanbanTui):
    config_path = (
        Path(__file__).parent.parent.parent / "sample-configs/sample_auth.toml"
    )
    os.environ["KANBAN_TUI_AUTH_FILE"] = config_path.as_posix()

    test_app.auth_only = True
    test_app.config.backend.mode = Backends.JIRA
    test_app.backend = test_app.get_backend()
    async with test_app.run_test(size=APP_SIZE) as pilot:
        assert pilot.app.auth_only
        assert isinstance(pilot.app.screen, ModalAuthScreen)
        assert pilot.app.screen.api_key == "MY_TEST_KEY"
        await pilot.press("e")
        await pilot.press(*"NEW_KEY")
        await pilot.press("enter")
        assert isinstance(pilot.app.focused, IconButton)

        assert pilot.app.screen.api_key == "NEW_KEY"
