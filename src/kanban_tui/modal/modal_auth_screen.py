import sys
from typing import Iterable, TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui

from rich.text import Text
from textual.reactive import reactive
from textual import on
from textual.widget import Widget
from textual.binding import Binding

from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Input, Label
from textual.containers import Horizontal, Vertical

from kanban_tui.widgets.custom_widgets import IconButton


class ApiKeyInput(Input):
    app: "KanbanTui"

    def on_mount(self):
        if self.value:
            self.disabled = True
        self.password = True
        self.placeholder = "Please enter a valid api key"


class ApiKeyWidget(Horizontal):
    app: "KanbanTui"
    BINDINGS = [
        Binding("e", "edit", "Edit"),
        Binding("space", "show_hide_key('show')", "Show Key", priority=True),
        Binding("space", "show_hide_key('hide')", "Hide Key", priority=True),
    ]

    def on_mount(self):
        has_api_key = bool(self.app.backend.api_key)
        self.can_focus = has_api_key
        self.query_one("#button_edit_api_key", IconButton).display = has_api_key

    def compose(self):
        yield ApiKeyInput(self.app.backend.api_key, id="input_api_key")
        yield IconButton(label=Text.from_markup(":pen:"), id="button_edit_api_key")
        yield IconButton(
            label=Text.from_markup(":clipboard:"), id="button_copy_api_key"
        )
        yield IconButton(label=Text.from_markup(":eye:"), id="button_show_api_key")

    @on(Button.Pressed, "#button_edit_api_key")
    def action_edit(self):
        input_widget = self.query_one(ApiKeyInput)
        input_widget.disabled = not input_widget.disabled
        self.query_one("#button_edit_api_key", IconButton).display = False

        if not input_widget.disabled:
            input_widget.focus()

    @on(Button.Pressed, "#button_copy_api_key")
    def action_copy(self, event: Button.Pressed):
        input_widget = self.query_one(ApiKeyInput)
        value = input_widget.value
        if sys.platform.startswith("darwin"):
            self.notify(
                message="Copying api key this way is not possible on [$warning]MacOs[/]",
                title="Functionality not supported",
                severity="warning",
            )
            return
        self.app.copy_to_clipboard(value)

        if not input_widget.disabled:
            input_widget.focus()

    @on(Button.Pressed, "#button_show_api_key")
    def action_show_hide_key(self, show: Literal["show", "hide"] | None = None):
        input_widget = self.query_one(ApiKeyInput)
        input_widget.password = not input_widget.password
        self.refresh_bindings()

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action == "show_hide_key":
            is_visible = self.query_one(ApiKeyInput).password
            if parameters == ("show",):
                return is_visible
            elif parameters == ("hide",):
                return not is_visible
        return True


class CertPathInput(Input):
    app: "KanbanTui"

    def on_mount(self):
        if self.value:
            self.disabled = True
        self.placeholder = "Please enter path to certificate"


class CertPathWidget(Horizontal):
    app: "KanbanTui"
    BINDINGS = [
        Binding("e", "edit", "Edit"),
    ]

    def on_mount(self):
        has_cert_path = bool(self.app.backend.cert_path)
        self.can_focus = has_cert_path
        self.query_one("#button_edit_cert_path", IconButton).display = has_cert_path

    def compose(self):
        yield CertPathInput(self.app.backend.cert_path, id="input_cert_path")
        yield IconButton(label=Text.from_markup(":pen:"), id="button_edit_cert_path")

    @on(Button.Pressed, "#button_edit_cert_path")
    def action_edit(self):
        input_widget = self.query_one(CertPathInput)
        input_widget.disabled = not input_widget.disabled
        self.query_one("#button_edit_cert_path", IconButton).display = False

        if not input_widget.disabled:
            input_widget.focus()


class AuthLabel(Label):
    app: "KanbanTui"

    def on_mount(self):
        path = self.app.backend.settings.auth_file_path
        self.update(f"Your Jira API Key is stored at [$warning]{path}[/]")


class ModalAuthScreen(ModalScreen):
    app: "KanbanTui"

    BINDINGS = [
        Binding("escape", "dismiss", "Close", priority=True),
    ]
    api_key: reactive[str] = reactive("")

    def on_mount(self):
        self.api_key = self.app.backend.api_key
        if not self.api_key:
            self.query_one("#button_show_api_key", IconButton).display = False
            self.notify(
                title="No api key found",
                message="Please enter a valid api key",
                severity="warning",
            )

    def compose(self) -> Iterable[Widget]:
        with Vertical():
            yield Footer()
            yield AuthLabel()
            yield Label("Api key:")
            yield ApiKeyWidget(classes="auth-widgets")

            yield Label("Path to certificate file")
            yield CertPathWidget(classes="auth-widgets")

    @on(Input.Submitted, "#input_api_key")
    def update_api_key(self, event: Input.Submitted):
        value = event.value
        self.app.backend.auth_settings.set_jira_api_key(value)

        self.notify(
            title="New api key saved",
            message="Press escape to close auth screen",
        )
        self.api_key = value

    @on(Input.Submitted, "#input_cert_path")
    def update_cert_path(self, event: Input.Submitted):
        value = event.value
        self.app.backend.auth_settings.set_jira_cert_path(value)

        self.notify(
            title="New certificate path saved",
            message="Press escape to close auth screen",
        )
        self.cert_path = value

    @on(Input.Submitted, "#input_api_key")
    @on(Input.Submitted, "#input_cert_path")
    def show_edit_button(self, event: Input.Changed):
        event.input.disabled = True
        self.query_one(
            f"#button_edit_{event.input.id.split('_', maxsplit=1)[1]}", IconButton
        ).focus().display = True

    @on(Input.Changed, "#input_api_key")
    def update_visibility_show_button(self, event: Input.Changed):
        should_be_visible = bool(event.value)
        self.query_one("#button_show_api_key", IconButton).display = should_be_visible
