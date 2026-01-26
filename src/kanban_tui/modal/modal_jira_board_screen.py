from kanban_tui.config import JqlEntry
from kanban_tui.widgets.custom_widgets import ButtonRow
from kanban_tui.classes.board import Board
from typing import Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui

from textual import on, work
from textual.widget import Widget
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Input, Button, Label, Static, ListView, ListItem
from textual.containers import Vertical, Horizontal
from textual.validation import Validator, ValidationResult

from kanban_tui.backends.jira.jira_api import get_jql, get_transitions


class JQLValidator(Validator):
    """Validator for JQL input - just checks it's not empty"""

    def validate(self, value: str) -> ValidationResult:
        if not value or value.strip() == "":
            return self.failure("JQL cannot be empty")
        return self.success()


class ModalNewJiraBoardScreen(ModalScreen):
    """Modal screen for creating a new Jira board based on JQL query"""

    app: "KanbanTui"
    BINDINGS = [Binding("escape", "app.pop_screen", "Close")]

    def __init__(self, board: Board | None = None) -> None:
        self.jira_board = board
        super().__init__()
        self.jql_validated = False
        self.detected_columns: list[str] = []

    def compose(self) -> Iterable[Widget]:
        with Vertical():
            yield Label("Create New Jira Board", id="label_header")
            yield Input(
                placeholder="Enter Board Name",
                id="input_board_name",
            )
            with Horizontal():
                yield Input(
                    placeholder="Enter JQL Query (e.g., project = MYPROJ AND status != Done)",
                    validators=[JQLValidator()],
                    validate_on=["changed"],
                    id="input_jql",
                )
                yield Button(
                    "Check", id="btn_check_jql", variant="primary", disabled=True
                )

            # Status/feedback area
            yield Static("Enter JQL and click 'Check' to validate", id="static_status")

            # Column list (hidden initially)
            with Vertical(id="column_container", classes="hidden"):
                yield Label("Detected Columns (from transitions):", id="label_columns")
                yield ListView(id="column_list")

            # Action buttons
            yield ButtonRow(id="horizontal_buttons")

    def board_to_jql(self, board: Board) -> JqlEntry:
        return [
            jql for jql in self.app.backend.settings.jqls if jql.id == board.board_id
        ][0]

    def on_mount(self) -> None:
        if self.jira_board:
            self.query_one("#input_board_name", Input).value = self.jira_board.name
            self.query_one("#input_jql", Input).value = self.board_to_jql(
                self.jira_board
            ).jql
            self.query_exactly_one("#btn_continue", Button).label = "Edit board"

        self.query_exactly_one("#input_jql", Input).border_title = "JQL Query"
        self.query_exactly_one("#input_board_name", Input).border_title = "Board Name"
        self.query_exactly_one("#btn_continue", Button).label = "Create board"
        self.query_exactly_one("#btn_continue", Button).disabled = True

    @on(Input.Changed, "#input_jql")
    def on_jql_changed(self, event: Input.Changed) -> None:
        """Enable check button when JQL is valid"""
        is_valid = event.validation_result and event.validation_result.is_valid
        self.query_exactly_one("#btn_check_jql", Button).disabled = not is_valid

        # Reset validation state when JQL changes
        if self.jql_validated:
            self.jql_validated = False
            self.detected_columns = []
            self.query_exactly_one("#column_container", Vertical).add_class("hidden")
            self.query_exactly_one("#btn_continue", Button).disabled = True
            self.query_exactly_one("#static_status", Static).update(
                "JQL changed - click 'Check' to re-validate"
            )

    @on(Input.Changed, "#input_board_name")
    def on_board_name_changed(self, event: Input.Changed) -> None:
        """Enable create button only if both name and JQL are valid"""
        board_name = event.input.value.strip()
        has_name = bool(board_name)

        # Only enable create if we have both name and validated JQL with columns
        self.query_exactly_one("#btn_continue", Button).disabled = not (
            has_name and self.jql_validated and self.detected_columns
        )

    @on(Button.Pressed, "#btn_check_jql")
    @work()
    async def check_jql(self) -> None:
        """Validate JQL by querying Jira and fetch transitions"""
        jql = self.query_exactly_one("#input_jql", Input).value
        status_widget = self.query_exactly_one("#static_status", Static)

        status_widget.update("⏳ Checking JQL query...")
        self.query_exactly_one("#btn_check_jql", Button).disabled = True

        try:
            # Execute JQL query
            result = get_jql(self.app.backend.auth, jql)
            issues = result.get("issues", [])

            if not issues:
                status_widget.update("❌ No issues found for this JQL query")
                self.jql_validated = False
                self.detected_columns = []
                self.query_exactly_one("#column_container", Vertical).add_class(
                    "hidden"
                )
                self.query_exactly_one("#btn_check_jql", Button).disabled = False
                return

            # Get transitions from the first issue to determine available columns
            first_issue_key = issues[0]["key"]

            try:
                transitions_data = get_transitions(
                    self.app.backend.auth, first_issue_key
                )
            except Exception as trans_error:
                # If we can't get transitions, just use current statuses
                self.app.notify(
                    f"Warning: Could not fetch transitions ({trans_error}). Using current statuses only.",
                    severity="warning",
                    timeout=5,
                )
                transitions_data = None

            # Extract unique status names from transitions
            # Transitions show where an issue can go, so we collect all target statuses
            unique_statuses = set()

            # Add current status of all issues
            for issue in issues:
                current_status = issue.get("fields", {}).get("status", {}).get("name")
                if current_status:
                    unique_statuses.add(current_status)

            # Add all possible transition target statuses
            # Handle different response formats
            if transitions_data is not None:
                if isinstance(transitions_data, list):
                    for transition in transitions_data:
                        # Skip if transition is not a dict
                        if not isinstance(transition, dict):
                            continue
                        to_status = transition.get("to", {})  # .get("name")
                        if to_status:
                            unique_statuses.add(to_status)
                elif isinstance(transitions_data, dict):
                    # Handle case where it might be wrapped in a dict
                    transitions_list = transitions_data.get("transitions", [])
                    for transition in transitions_list:
                        if not isinstance(transition, dict):
                            continue
                        to_status = transition.get("to", {}).get("name")
                        if to_status:
                            unique_statuses.add(to_status)

            self.detected_columns = sorted(unique_statuses)

            if not self.detected_columns:
                status_widget.update("❌ No status transitions found")
                self.jql_validated = False
                self.query_exactly_one("#btn_check_jql", Button).disabled = False
                return

            # Display success and show columns
            status_widget.update(f"✅ JQL valid - Found {len(issues)} issue(s)")
            self.jql_validated = True

            # Populate column list
            column_list = self.query_exactly_one("#column_list", ListView)
            await column_list.clear()
            for status in self.detected_columns:
                await column_list.append(ListItem(Label(status)))

            # Show column container
            self.query_exactly_one("#column_container", Vertical).remove_class("hidden")

            # Enable create button if board name is also filled
            board_name = self.query_exactly_one(
                "#input_board_name", Input
            ).value.strip()
            self.query_exactly_one("#btn_continue", Button).disabled = not bool(
                board_name
            )

        except Exception as e:
            status_widget.update(f"❌ Error: {str(e)}")
            self.jql_validated = False
            self.detected_columns = []
            self.query_exactly_one("#column_container", Vertical).add_class("hidden")

        finally:
            self.query_exactly_one("#btn_check_jql", Button).disabled = False

    @on(Button.Pressed, "#btn_continue")
    def create_board(self) -> None:
        """Create the new Jira board with the validated JQL and detected columns"""
        board_name = self.query_exactly_one("#input_board_name", Input).value.strip()
        jql = self.query_exactly_one("#input_jql", Input).value

        if not board_name or not self.jql_validated or not self.detected_columns:
            return

        # Add to config
        new_board_id = self.app.backend.create_new_board(name=board_name, jql=jql)
        # self.app.config.add_jql(new_jql_entry)

        self.app.config.set_active_jql(new_board_id)
        self.app.config.save()
        self.app.update_board_list()

        self.dismiss(result=True)

    @on(Button.Pressed, "#btn_cancel")
    def cancel(self) -> None:
        """Cancel board creation"""
        self.dismiss(result=None)
