from kanban_tui.widgets.settings_widgets import RepositionButton
from kanban_tui.config import JqlEntry
from kanban_tui.widgets.custom_widgets import ButtonRow
from kanban_tui.classes.board import Board
from typing import Iterable, TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui

from textual import on, work
from textual.widget import Widget
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Input, Button, Label, Static, ListView, ListItem
from textual.containers import Vertical, Horizontal, VerticalGroup
from textual.validation import Validator, ValidationResult
from rich.text import Text

from kanban_tui.backends.jira.jira_api import (
    get_jql,
    get_transitions_async,
)


class JQLValidator(Validator):
    """Validator for JQL input - just checks it's not empty"""

    def validate(self, value: str) -> ValidationResult:
        if not value or value.strip() == "":
            return self.failure("JQL cannot be empty")
        return self.success()


class JiraColumnList(ListView):
    app: "KanbanTui"
    BINDINGS = [
        Binding(key="j", action="cursor_down", show=False),
        Binding(key="k", action="cursor_up", show=False),
    ]

    # Actions
    def action_cursor_down(self) -> None:
        self.refresh_bindings()
        return super().action_cursor_down()

    def action_cursor_up(self) -> None:
        self.refresh_bindings()
        return super().action_cursor_up()


class JiraColumnListItem(ListItem):
    """List item for a Jira status/column with reordering buttons"""

    def __init__(self, status: str, position: int, total_columns: int) -> None:
        self.status = status
        self.position = position
        self.total_columns = total_columns
        super().__init__(id=f"listitem_status_{position}")

    def compose(self) -> Iterable[Widget]:
        with Horizontal():
            with VerticalGroup():
                yield RepositionButton(
                    label=Text.from_markup(":arrow_up_small:"),
                    id=f"button_up_{self.position}",
                    classes="invisible" if self.position == 0 else "",
                )
                yield RepositionButton(
                    label=Text.from_markup(":arrow_down_small:"),
                    id=f"button_down_{self.position}",
                    classes="invisible"
                    if self.position == self.total_columns - 1
                    else "",
                )
            yield Label(f"Column {self.position + 1}: {self.status}")


class ModalNewJiraBoardScreen(ModalScreen):
    """Modal screen for creating a new Jira board based on JQL query"""

    app: "KanbanTui"
    BINDINGS = [
        Binding(key="escape", action="app.pop_screen", description="Close"),
        Binding(key="j", action="cursor_down", show=False),
        Binding(key="k", action="cursor_up", show=False),
        Binding(
            key="J", action="move_column_down", description="Move down", show=False
        ),
        Binding(key="K", action="move_column_up", description="Move up", show=False),
    ]

    def __init__(self, board: Board | None = None) -> None:
        self.jira_board = board
        super().__init__()
        self.jql_validated = False
        self.detected_columns: list[str] = []
        self.column_order: list[str] = []  # Track the current order of columns

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
                yield Label(
                    "Detected Columns (move with j/k, reorder with J/K):",
                    id="label_columns",
                )
                yield JiraColumnList(id="column_list")

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
                transitions_data = get_transitions_async(
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
            self.column_order = list(self.detected_columns)  # Initialize order

            if not self.detected_columns:
                status_widget.update("❌ No status transitions found")
                self.jql_validated = False
                self.query_exactly_one("#btn_check_jql", Button).disabled = False
                return

            # Display success and show columns
            status_widget.update(f"✅ JQL valid - Found {len(issues)} issue(s)")
            self.jql_validated = True

            # Populate column list with reorderable items
            await self._refresh_column_list()

            # Show column container
            self.query_exactly_one("#column_container", Vertical).remove_class("hidden")

            # Enable create button if board name is also filled
            board_name = self.query_exactly_one(
                "#input_board_name", Input
            ).value.strip()
            self.query_exactly_one("#btn_continue", Button).disabled = not bool(
                board_name
            )
            self.call_after_refresh(callback=self.query_one(JiraColumnList).focus)

        except Exception as e:
            status_widget.update(f"❌ Error: {str(e)}")
            self.jql_validated = False
            self.detected_columns = []
            self.query_exactly_one("#column_container", Vertical).add_class("hidden")

        finally:
            self.query_exactly_one("#btn_check_jql", Button).disabled = False

    async def _refresh_column_list(self):
        """Refresh the column list display with current order"""
        column_list = self.query_exactly_one("#column_list", ListView)
        await column_list.clear()

        for i, status in enumerate(self.column_order):
            await column_list.append(
                JiraColumnListItem(status, i, len(self.column_order))
            )
        column_list.index = 0

    async def _move_column(self, direction: Literal["up", "down"]):
        """Move the currently selected column up or down"""
        column_list = self.query_exactly_one("#column_list", ListView)
        current_index = column_list.index

        if current_index is None or current_index < 0:
            return

        if direction == "up" and current_index == 0:
            return
        if direction == "down" and current_index >= len(self.column_order) - 1:
            return

        # Swap positions
        new_index = current_index - 1 if direction == "up" else current_index + 1
        self.column_order[current_index], self.column_order[new_index] = (
            self.column_order[new_index],
            self.column_order[current_index],
        )

        # Refresh the list and restore selection
        await self._refresh_column_list()
        column_list.index = new_index

    @on(Button.Pressed)
    async def handle_button_press(self, event: Button.Pressed):
        """Handle up/down arrow button presses"""
        button_id = event.button.id

        if button_id and button_id.startswith("button_up_"):
            await self._move_column("up")
        elif button_id and button_id.startswith("button_down_"):
            await self._move_column("down")

    def action_move_column_up(self):
        """Action to move column up with keyboard"""
        self.run_worker(self._move_column("up"))

    def action_move_column_down(self):
        """Action to move column down with keyboard"""
        self.run_worker(self._move_column("down"))

    @on(Button.Pressed, "#btn_continue")
    def create_board(self) -> None:
        """Create the new Jira board with the validated JQL and detected columns"""
        board_name = self.query_exactly_one("#input_board_name", Input).value.strip()
        jql = self.query_exactly_one("#input_jql", Input).value

        if not board_name or not self.jql_validated or not self.column_order:
            return

        # Create column mapping based on the final order
        column_mapping = {
            status: idx + 1 for idx, status in enumerate(self.column_order)
        }

        # Add to config with column mapping
        new_board_id = self.app.backend.create_new_board(
            name=board_name, jql=jql, column_mapping=column_mapping
        )

        self.app.config.set_active_jql(new_board_id)
        self.app.config.save()
        self.app.update_board_list()

        self.dismiss(result=new_board_id)

    @on(Button.Pressed, "#btn_cancel")
    def cancel(self) -> None:
        """Cancel board creation"""
        self.dismiss(result=None)
