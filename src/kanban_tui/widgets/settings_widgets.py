from __future__ import annotations
from typing import Iterable, TYPE_CHECKING, Literal

from kanban_tui.config import MovementModes
from kanban_tui.widgets.modal_task_widgets import VimSelect

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui

from textual import on
from textual.message import Message
from textual.events import DescendantBlur
from textual.reactive import reactive
from textual.binding import Binding
from textual.widget import Widget
from textual.widgets import (
    Label,
    Select,
    Switch,
    Input,
    Rule,
    Button,
    ListView,
    ListItem,
)
from textual.containers import Horizontal, Vertical
from rich.text import Text

from kanban_tui.modal.modal_color_pick import TitleInput
from kanban_tui.modal.modal_settings import ModalUpdateColumnScreen
from kanban_tui.modal.modal_task_screen import ModalConfirmScreen
from kanban_tui.classes.column import Column
from kanban_tui.backends.sqlite.database import (
    update_column_name_db,
    update_column_visibility_db,
    delete_column_db,
    create_new_column_db,
    update_column_positions_db,
    update_status_update_columns_db,
)


class DataBasePathInput(Horizontal):
    app: "KanbanTui"

    def on_mount(self):
        self.border_title = "database.database_path [yellow on black]^d[/]"

    def compose(self) -> Iterable[Widget]:
        yield Label("Database File")
        with self.prevent(Input.Changed):
            yield Input(
                value=self.app.config.backend.sqlite_settings.database_path,
                select_on_focus=False,
                id="input_database_path",
            )
        return super().compose()


class TaskMovementSelector(Horizontal):
    app: "KanbanTui"

    def on_mount(self):
        self.border_title = "task.movement_mode [yellow on black]^n[/]"

    def compose(self) -> Iterable[Widget]:
        yield Label("Task movement_mode")
        with self.prevent(Select.Changed):
            yield VimSelect.from_values(
                MovementModes,
                value=self.app.config.task.movement_mode,
                id="select_movement_mode",
                allow_blank=False,
            )

    @on(Select.Changed)
    def update_config(self, event: Select.Changed):
        self.app.config.set_task_movement_mode(new_mode=event.value)


class BoardColumnsInView(Horizontal):
    app: "KanbanTui"

    def on_mount(self):
        self.border_title = "board.columns_in_view [yellow on black]^b[/]"

    def compose(self) -> Iterable[Widget]:
        yield Label("Columns in view")
        with self.prevent(Select.Changed):
            yield VimSelect.from_values(
                [i + 1 for i in range(len(self.app.column_list))],
                value=self.app.config.board.columns_in_view,
                id="select_columns_in_view",
                allow_blank=False,
            )

    @on(Select.Changed)
    def update_config(self, event: Select.Changed):
        self.app.config.set_columns_in_view(event.select.value)


class TaskAlwaysExpandedSwitch(Horizontal):
    app: "KanbanTui"

    def on_mount(self):
        self.border_title = "task.always_expanded [yellow on black]^e[/]"

    def compose(self) -> Iterable[Widget]:
        yield Label("Always Expand Tasks")
        yield Switch(
            value=self.app.config.task.always_expanded, id="switch_expand_tasks"
        )
        return super().compose()

    @on(Switch.Changed)
    def update_config(self, event: Switch.Changed):
        self.app.config.set_task_always_expanded(new_value=event.value)


class DefaultTaskColorSelector(Horizontal):
    app: "KanbanTui"

    def on_mount(self) -> None:
        self.query_one(TitleInput).background = self.app.config.task.default_color
        self.border_title = "task.default_color [yellow on black]^g[/]"

    def compose(self) -> Iterable[Widget]:
        yield Label("Default Task Color")
        with self.prevent(Input.Changed):  # prevent config change on init
            yield TitleInput(
                value=self.app.config.task.default_color, id="task_color_preview"
            )

    @on(Input.Changed)
    def update_input_color(self, event: Input.Changed):
        try:
            self.query_one(TitleInput).background = event.input.value
            self.app.config.set_task_default_color(new_color=event.input.value)
            event.input.styles.border = "tall", "green"
            event.input.border_subtitle = None
            event.input.border_title = None
        # Todo add validator to input?
        except Exception:
            event.input.styles.border = "tall", "red"
            event.input.border_subtitle = "invalid color value"
            event.input.border_title = (
                f"last valid: {self.app.config.task.default_color}"
            )

    @on(DescendantBlur)
    def reset_color(self):
        self.query_one(TitleInput).value = self.app.config.task.default_color


# Widget to Add new columns and change column visibility
# Select Widget, visible Green, not visible red
class AddRule(Rule):
    class Pressed(Message):
        def __init__(self, addrule: AddRule) -> None:
            self.addrule = addrule
            super().__init__()

        @property
        def control(self):
            return self.addrule

    def __init__(self, column: Column | None = None) -> None:
        self.column = column
        self.position = self.column.position if self.column else 0

        super().__init__(id=f"addrule_{self.column.position if self.column else 0}")

    def compose(self) -> Iterable[Widget]:
        yield Button("+")
        return super().compose()

    @on(Button.Pressed)
    def send_message_to_add_column(self):
        self.post_message(self.Pressed(self))


class ColumnListItem(ListItem):
    app: "KanbanTui"

    class Deleted(Message):
        def __init__(self, column_list_item: ColumnListItem) -> None:
            self.column_list_item = column_list_item
            super().__init__()

        @property
        def control(self):
            return self.column_list_item

    def __init__(self, column: Column) -> None:
        self.column = column
        super().__init__(id=f"listitem_column_{self.column.column_id}")

    def compose(self) -> Iterable[Widget]:
        with Horizontal():
            yield Label(Text.from_markup(f"Show [cyan]{self.column.name}[/]"))
            yield Switch(
                value=self.column.visible,
                id=f"switch_col_vis_{self.column.column_id}",
            )
            yield Button(
                label="Delete",
                id=f"button_col_del_{self.column.column_id}",
                variant="error",
            )
        yield AddRule(column=self.column)

    @on(Button.Pressed)
    def trigger_column_delete(self, event: Button.Pressed):
        if event.button.id:
            self.post_message(self.Deleted(self))


class FirstListItem(ListItem):
    app: "KanbanTui"

    def __init__(self) -> None:
        super().__init__(id="listitem_column_0")

    def compose(self) -> Iterable[Widget]:
        yield AddRule()

        return super().compose()


class ColumnSelector(ListView):
    """Widget to add/delete/rename columns and change the column visibility"""

    app: "KanbanTui"

    BINDINGS = [
        Binding(key="j", action="cursor_down", show=False),
        Binding(key="k", action="cursor_up", show=False),
        Binding(key="enter,space", action="select_cursor", show=False),
        Binding(key="d", action="delete_press", description="Delete Column", show=True),
        Binding(
            key="r", action="rename_column", description="Rename Column", show=True
        ),
        Binding(
            key="n", action="addrule_press", description="Insert Column", show=True
        ),
    ]
    amount_visible: reactive[int] = reactive(0)

    def on_mount(self) -> None:
        self.border_title = "column.visibility [yellow on black]^c[/]"
        self.amount_visible = len(self.app.visible_column_dict)

    def __init__(self, *args, **kwargs) -> None:
        children = [FirstListItem()] + [
            ColumnListItem(column=column) for column in self.app.column_list
        ]
        super().__init__(*children, id="column_list", initial_index=0, *args, **kwargs)

    # rename Column
    def action_rename_column(self):
        if not isinstance(self.highlighted_child, ColumnListItem):
            return

        async def modal_rename_column(
            event_col_name: tuple[Column, str] | None,
        ):
            if event_col_name:
                column, new_column_name = event_col_name
                update_column_name_db(
                    column_id=column.column_id,
                    new_column_name=new_column_name,
                    database=self.app.config.backend.sqlite_settings.database_path,
                )

                # Update state and Widgets
                self.app.update_column_list()
                await self.clear()
                await self.extend(
                    [FirstListItem()]
                    + [ColumnListItem(column=column) for column in self.app.column_list]
                )
                await self.app.screen.query_one(StatusColumnSelector).recompose()
                self.app.screen.query_one(
                    StatusColumnSelector
                ).get_select_widget_values()
                # Trigger Update on tab Switch
                self.app.config_has_changed = True

                self.index = column.position

                # self.notify(
                #     title="Columns Updated",
                #     message=f"Column [blue]{column_name}[/] renamed to [blue]{new_column_name}[/]",
                #     timeout=1,
                # )

        self.app.push_screen(
            ModalUpdateColumnScreen(column=self.highlighted_child.column),
            callback=modal_rename_column,
        )

    # New Column
    def action_addrule_press(self):
        if self.highlighted_child is None:
            return
        self.highlighted_child.query_one(AddRule).query_one(Button).press()

    @on(AddRule.Pressed)
    def add_new_column(self, event: AddRule.Pressed):
        async def modal_add_new_column(
            event_col_name: tuple[AddRule.Pressed, str] | None,
        ):
            if event_col_name:
                event, column_name = event_col_name
                update_column_positions_db(
                    board_id=self.app.active_board.board_id,
                    new_position=event.addrule.position,
                    database=self.app.config.backend.sqlite_settings.database_path,
                )
                create_new_column_db(
                    board_id=self.app.active_board.board_id,
                    position=event.addrule.position + 1,
                    name=column_name,
                    visible=True,
                    database=self.app.config.backend.sqlite_settings.database_path,
                )
                self.app.update_column_list()
                await self.clear()
                await self.extend(
                    [FirstListItem()]
                    + [ColumnListItem(column=column) for column in self.app.column_list]
                )
                self.index = event.addrule.position + 1
                self.amount_visible += 1

        self.app.push_screen(
            ModalUpdateColumnScreen(event=event), callback=modal_add_new_column
        )

    # Delete Column
    def action_delete_press(self):
        if isinstance(self.highlighted_child, ColumnListItem):
            self.highlighted_child.query_one(Button).press()

    @on(ColumnListItem.Deleted)
    def delete_column(self, event: ColumnListItem.Deleted):
        column_name = event.column_list_item.column.name
        if (
            len([task for task in self.app.task_list if task.column == column_name])
            != 0
        ):
            self.send_error_notify(column_name)
            return

        async def modal_delete_column(
            event: ColumnListItem.Deleted, delete_yn: bool
        ) -> None:
            if delete_yn:
                column_id = event.column_list_item.column.column_id
                column_name = event.column_list_item.column.name

                delete_column_db(
                    column_id=column_id,
                    database=self.app.config.backend.sqlite_settings.database_path,
                )
                self.app.update_column_list()
                if event.column_list_item.column.visible:
                    self.amount_visible -= 1
                else:
                    self.watch_amount_visible()

                # Remove ListItem
                await event.column_list_item.remove()

                self.notify(
                    title="Columns Updated",
                    message=f"Column [blue]{column_name}[/] deleted",
                    timeout=2,
                )

        self.app.push_screen(
            ModalConfirmScreen(text=f"Delete Column [blue]{column_name}[/]"),
            callback=lambda x: modal_delete_column(event=event, delete_yn=x),
        )

    def send_error_notify(self, column_name: str):
        self.notify(
            title="Column not empty",
            message=f"Remove all tasks in column [blue]{column_name}[/] before deletion",
            timeout=1,
            severity="error",
        )

    def watch_amount_visible(self):
        self.border_title = f"columns.visible  [cyan]{self.amount_visible} / {len(self.app.column_list)}[/] [yellow on black]^c[/]"

    @on(ListView.Selected)
    def on_space_key(self, event: ListView.Selected):
        if isinstance(event.list_view.highlighted_child, FirstListItem):
            self.action_addrule_press()
        else:
            if event.list_view.highlighted_child:
                event.list_view.highlighted_child.query_one(Switch).toggle()

    @on(Switch.Changed)
    def update_visibility(self, event: Switch.Changed):
        if event.switch.id is None:
            return
        self.amount_visible += 1 if event.value else -1
        column_id = int(event.switch.id.split("_")[-1])
        update_column_visibility_db(
            column_id=column_id,
            visible=event.value,
            database=self.app.config.backend.sqlite_settings.database_path,
        )

        self.app.update_column_list()


class StatusColumnSelector(Vertical):
    app: "KanbanTui"
    """Widget to select the columns, which are used to update the start/finish dates on tasks"""

    def on_mount(self):
        self.border_title = "column.status_update [yellow on black]^s[/]"
        with self.prevent(Select.Changed):
            self.get_select_widget_values()

    def compose(self) -> Iterable[Widget]:
        with Horizontal(classes="setting-horizontal"):
            yield Label("Reset")
            yield VimSelect(
                [
                    (Text.from_markup(column.name), column.column_id)
                    for column in self.app.column_list
                ],
                # value=self.app.active_board.reset_column or BLANK,
                prompt="No reset column",
                id="select_reset",
            )
        with Horizontal(classes="setting-horizontal"):
            yield Label("Start")
            yield VimSelect(
                [
                    (Text.from_markup(column.name), column.column_id)
                    for column in self.app.column_list
                ],
                # value=self.app.active_board.start_column or BLANK,
                prompt="No start column",
                id="select_start",
            )
        with Horizontal(classes="setting-horizontal"):
            yield Label("Finish")
            yield VimSelect(
                [
                    (Text.from_markup(column.name), column.column_id)
                    for column in self.app.column_list
                ],
                # value=self.app.active_board.finish_column or BLANK,
                prompt="No finish column",
                id="select_finish",
            )

    @on(Select.Changed)
    def update_status_columns(self, event: Select.Changed):
        if event.select.id is None:
            return
        update_status_update_columns_db(
            new_status=event.select.selection,  # type: ignore
            column_prefix=event.select.id.split("_")[-1],
            board_id=self.app.active_board.board_id,
            database=self.app.config.backend.sqlite_settings.database_path,
        )

        self.app.update_board_list()

        if not event.select.selection:
            return

        # If column is already selected, clear the old column
        for other_select in self.query(Select).exclude(f"#{event.select.id}"):
            if other_select.id is None:
                continue
            if event.value == other_select.value:
                other_select.clear()
                self.notify(
                    title="Status update column cleared",
                    message=f"Status update for [yellow]{other_select.id.split('_')[1]}[/] was removed",
                    severity="warning",
                )

    def get_select_widget_values(self):
        if self.app.active_board.reset_column is not None:
            self.query_exactly_one(
                "#select_reset", Select
            ).value = self.app.active_board.reset_column

        if self.app.active_board.start_column is not None:
            self.query_exactly_one(
                "#select_start", Select
            ).value = self.app.active_board.start_column

        if self.app.active_board.finish_column is not None:
            self.query_exactly_one(
                "#select_finish", Select
            ).value = self.app.active_board.finish_column


class SettingsView(Vertical):
    BINDINGS = [
        Binding(
            key="ctrl+d", action="quick_focus_setting('db')", show=False, priority=True
        ),
        Binding(
            key="ctrl+e",
            action="quick_focus_setting('expand')",
            show=False,
            priority=True,
        ),
        Binding(
            key="ctrl+n",
            action="quick_focus_setting('movement_mode')",
            show=False,
            priority=True,
        ),
        Binding(
            key="ctrl+b",
            action="quick_focus_setting('columns_in_view')",
            show=False,
            priority=True,
        ),
        Binding(
            key="ctrl+g",
            action="quick_focus_setting('defaultcolor')",
            show=False,
            priority=True,
        ),
        Binding(
            key="ctrl+c",
            action="quick_focus_setting('columns')",
            show=False,
            priority=True,
        ),
        Binding(
            key="ctrl+s",
            action="quick_focus_setting('status')",
            show=False,
            priority=True,
        ),
    ]
    config_has_changed: reactive[bool] = reactive(False, init=False)

    def compose(self) -> Iterable[Widget]:
        yield DataBasePathInput(classes="setting-block")
        with Horizontal(classes="setting-horizontal"):
            yield TaskAlwaysExpandedSwitch(classes="setting-block")
            yield TaskMovementSelector(classes="setting-block")
        with Horizontal(classes="setting-horizontal"):
            yield DefaultTaskColorSelector(classes="setting-block")
            yield BoardColumnsInView(classes="setting-block")
        with Horizontal(classes="setting-horizontal"):
            yield StatusColumnSelector(classes="setting-block")
            yield ColumnSelector(classes="setting-block")

    @on(Input.Changed)
    @on(Switch.Changed)
    @on(Button.Pressed)
    @on(Select.Changed)
    def config_changes(self):
        self.config_has_changed = True

    def action_quick_focus_setting(
        self,
        block: Literal[
            "db",
            "expand",
            "movement_mode",
            "defaultcolor",
            "columns",
            "status",
            "columns_in_view",
        ],
    ):
        match block:
            case "db":
                self.query_one(DataBasePathInput).query_one(Input).focus()
            case "expand":
                self.query_one(TaskAlwaysExpandedSwitch).query_one(Switch).focus()
            case "columns_in_view":
                self.query_one(BoardColumnsInView).query_one(Select).focus()
            case "movement_mode":
                self.query_one(TaskMovementSelector).query_one(Select).focus()
            case "defaultcolor":
                self.query_one(DefaultTaskColorSelector).query_one(Input).focus()
            case "columns":
                self.query_one(ColumnSelector).focus()
            case "status":
                self.query_one(StatusColumnSelector).query(Select).focus()
