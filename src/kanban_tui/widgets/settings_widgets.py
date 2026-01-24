from __future__ import annotations
from typing import Iterable, TYPE_CHECKING, Literal


if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui

from textual import on, work
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
from textual.containers import Horizontal, Vertical, VerticalGroup
from rich.text import Text

from kanban_tui.config import MovementModes
from kanban_tui.widgets.modal_task_widgets import VimSelect
from kanban_tui.widgets.custom_widgets import IconButton
from kanban_tui.modal.modal_category_screen import IsValidColor
from kanban_tui.modal.modal_settings import ModalUpdateColumnScreen
from kanban_tui.modal.modal_confirm_screen import ModalConfirmScreen
from kanban_tui.classes.column import Column
from kanban_tui.backends.sqlite.database import (
    switch_column_positions_db,
    update_status_update_columns_db,
)


class DataBasePathInput(Horizontal):
    app: "KanbanTui"

    def on_mount(self):
        self.border_title = "database.database_path"

    def compose(self) -> Iterable[Widget]:
        yield Label("Database File")
        with self.prevent(Input.Changed):
            yield Input(
                value=self.app.backend.database_path,
                select_on_focus=False,
                id="input_database_path",
            )
        return super().compose()


class TaskMovementSelector(Horizontal):
    app: "KanbanTui"

    def on_mount(self):
        self.border_title = "task.movement_mode"

    def compose(self) -> Iterable[Widget]:
        yield Label("Task movement_mode")
        with self.prevent(Select.Changed):
            movement_select = VimSelect.from_values(
                MovementModes,
                value=self.app.config.task.movement_mode,
                id="select_movement_mode",
                allow_blank=False,
            )
            movement_select.jump_mode = "focus"
            yield movement_select

    @on(Select.Changed)
    def update_config(self, event: Select.Changed):
        self.app.config.set_task_movement_mode(new_mode=event.value)


class BoardColumnsInView(Horizontal):
    app: "KanbanTui"

    def on_mount(self):
        self.border_title = "board.columns_in_view"
        self.set_initial_select_value()

    def compose(self) -> Iterable[Widget]:
        yield Label("Columns in view")
        with self.prevent(Select.Changed):
            column_select = VimSelect.from_values(
                [i + 1 for i in range(len(self.app.column_list))],
                id="select_columns_in_view",
                allow_blank=False,
            )
        column_select.jump_mode = "focus"
        yield column_select

    @on(Select.Changed)
    def update_config(self, event: Select.Changed):
        self.app.config.set_columns_in_view(event.select.value)

    def set_initial_select_value(self):
        select = self.query_one(Select)
        amount_cols = len(self.app.column_list)
        if self.app.config.board.columns_in_view > amount_cols:
            select.value = amount_cols
        else:
            with self.prevent(Select.Changed):
                select.value = self.app.config.board.columns_in_view


class TaskAlwaysExpandedSwitch(Horizontal):
    app: "KanbanTui"

    def on_mount(self):
        self.border_title = "task.always_expanded"

    def compose(self) -> Iterable[Widget]:
        yield Label("Always Expand Tasks")
        expand_switch = Switch(
            value=self.app.config.task.always_expanded, id="switch_expand_tasks"
        )
        expand_switch.jump_mode = "focus"
        yield expand_switch

    @on(Switch.Changed)
    def update_config(self, event: Switch.Changed):
        self.app.config.set_task_always_expanded(new_value=event.value)


class TaskDefaultColorSelector(Horizontal):
    app: "KanbanTui"

    def compose(self) -> Iterable[Widget]:
        yield Label("Default Task Color")
        with self.prevent(Input.Changed):  # prevent config change on init
            color_input = Input(
                value=self.app.config.task.default_color,
                id="task_color_preview",
                validators=[IsValidColor()],
                validate_on=["changed", "blur"],
            )
            color_input.jump_mode = "focus"
            yield color_input

    def on_mount(self) -> None:
        self.query_one(Input).styles.background = self.app.config.task.default_color
        self.border_title = "task.default_color"

    @on(Input.Changed)
    def update_input_color(self, event: Input.Changed):
        if event.validation_result and event.validation_result.is_valid:
            event.input.styles.background = event.input.value
            self.app.config.set_task_default_color(new_color=event.input.value)
        else:
            event.input.styles.background = self.app.config.task.default_color

    @on(DescendantBlur)
    def reset_color(self):
        self.query_one(Input).value = self.app.config.task.default_color


# Widget to Add new columns
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

    @on(Button.Pressed)
    def send_message_to_add_column(self, event: Button.Pressed):
        # Stop propagating the Button event to parents
        event.stop()
        self.post_message(self.Pressed(self))


class RepositionButton(Button): ...


class ColumnListItem(ListItem):
    app: "KanbanTui"
    column_visible: reactive[bool] = reactive(True, init=False)

    class Triggered(Message):
        def __init__(
            self,
            column_list_item: ColumnListItem,
            interaction: Literal["del", "vis", "rename", "up", "down"],
        ) -> None:
            self.interaction = interaction
            self.column_list_item = column_list_item
            super().__init__()

        @property
        def control(self):
            return self.column_list_item

    def __init__(self, column: Column) -> None:
        self.column = column
        super().__init__(id=f"listitem_column_{self.column.column_id}")
        self.column_visible = self.column.visible

    def compose(self) -> Iterable[Widget]:
        with Horizontal():
            with VerticalGroup():
                yield RepositionButton(
                    label=Text.from_markup(":arrow_up_small:"),
                    id=f"button_col_up_{self.column.column_id}",
                    classes="invisible" if self.column.position == 1 else None,
                )
                yield RepositionButton(
                    label=Text.from_markup(":arrow_down_small:"),
                    id=f"button_col_down_{self.column.column_id}",
                    classes="invisible"
                    if self.column.position == len(self.app.column_list)
                    else None,
                )
            yield Label(Text.from_markup(f"Show [cyan]{self.column.name}[/]"))

            vis_button = IconButton(
                label=Text.from_markup(":eye:"),
                id=f"button_col_vis_{self.column.column_id}",
                classes="shown" if self.column_visible else None,
            )
            vis_button.tooltip = "Toggle visibility"
            yield vis_button

            edit_button = IconButton(
                label=Text.from_markup(":pen:"),
                id=f"button_col_rename_{self.column.column_id}",
            )
            edit_button.tooltip = "Rename column"
            yield edit_button

            delete_button = IconButton(
                label=Text.from_markup(":wastebasket:"),
                id=f"button_col_del_{self.column.column_id}",
            )
            delete_button.tooltip = "Delete column"
            yield delete_button
        yield AddRule(column=self.column)

    def watch_column_visible(self):
        if not self.is_mounted:
            return
        self.query_one(f"#button_col_vis_{self.column.column_id}", Button).toggle_class(
            "shown"
        )

    @on(Button.Pressed)
    def trigger_button_interaction(self, event: Button.Pressed):
        interaction = event.button.id.split("_")[2]
        self.post_message(self.Triggered(self, interaction=interaction))


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
    jump_mode = "focus"

    BINDINGS = [
        Binding(key="j", action="cursor_down", show=False),
        Binding(key="k", action="cursor_up", show=False),
        Binding(
            key="J",
            action="move_column_position('down')",
            description="Move down",
            show=True,
        ),
        Binding(
            key="K",
            action="move_column_position('up')",
            description="Move up",
            show=True,
        ),
        Binding(key="enter,space", action="select_cursor", show=False),
        Binding(key="d", action="delete_press", description="Delete", show=True),
        Binding(key="r", action="rename_column", description="Rename", show=True),
        Binding(key="n", action="addrule_press", description="New Column", show=True),
    ]
    amount_visible: reactive[int] = reactive(0)

    def on_mount(self) -> None:
        self.border_title = "column.visibility"
        self.amount_visible = len(self.app.visible_column_dict)

    def __init__(self, *args, **kwargs) -> None:
        children = [FirstListItem()] + [
            ColumnListItem(column=column) for column in self.app.column_list
        ]
        super().__init__(*children, id="column_list", initial_index=0, *args, **kwargs)

    # Actions
    def action_cursor_down(self) -> None:
        self.refresh_bindings()
        return super().action_cursor_down()

    def action_cursor_up(self) -> None:
        self.refresh_bindings()
        return super().action_cursor_up()

    async def action_move_column_position(self, direction: Literal["up", "down"]):
        await self.move_column_position(
            column_list_item=self.highlighted_child, direction=direction
        )

    def action_rename_column(self):
        self.rename_column(self.highlighted_child)

    def action_addrule_press(self):
        if self.highlighted_child is None:
            return
        self.highlighted_child.query_one(AddRule).query_one(Button).press()

    async def action_delete_press(self):
        self.delete_column(self.highlighted_child)

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action in ["rename_column", "delete_press"]:
            return self.index != 0
        if "up" in parameters:
            return (self.index is not None) and (self.index > 1)
        if "down" in parameters:
            return self.index not in [0, len(self.app.column_list)]
        return True

    @work()
    async def rename_column(self, column_list_item: ColumnListItem):
        column_name = await self.app.push_screen(
            ModalUpdateColumnScreen(column=column_list_item.column),
            wait_for_dismiss=True,
        )
        if column_name is None:
            return

        self.app.backend.update_column_name(
            column_id=column_list_item.column.column_id,
            new_name=column_name,
        )

        # Update state and Widgets
        await self.update_columns()
        await self.update_dependent_widgets()

        self.app.needs_refresh = True
        self.index = column_list_item.column.position

    @on(AddRule.Pressed)
    @work()
    async def add_new_column(self, event: AddRule.Pressed):
        column_name = await self.app.push_screen(
            ModalUpdateColumnScreen(event=event), wait_for_dismiss=True
        )
        if column_name is None:
            return

        self.app.backend.create_new_column(
            board_id=self.app.active_board.board_id,
            position=event.addrule.position + 1,
            name=column_name,
        )

        await self.update_columns()
        await self.update_dependent_widgets()

        self.index = event.addrule.position + 1
        self.amount_visible += 1
        self.app.needs_refresh = True

    @work()
    async def delete_column(self, column_list_item: ColumnListItem):
        column = column_list_item.column
        if (
            len(
                [task for task in self.app.task_list if task.column == column.column_id]
            )
            != 0
        ):
            self.send_error_notify(column.name)
            return

        confirm_deletion = await self.app.push_screen(
            ModalConfirmScreen(
                text=f"Delete column [blue]{column.name}[/]",
                button_text="Delete column",
            ),
            wait_for_dismiss=True,
        )
        if not confirm_deletion:
            return

        deleted_column = self.app.backend.delete_column(
            column_id=column_list_item.column.column_id,
            position=column_list_item.column.position,
            board_id=self.app.active_board.board_id,
        )

        self.app.update_board_list()
        await self.update_columns()
        await self.update_dependent_widgets()

        if column_list_item.column.visible:
            self.amount_visible -= 1
        else:
            self.watch_amount_visible()

        self.notify(
            title="Columns Updated",
            message=f"Column [blue]{deleted_column.name}[/] deleted",
            timeout=2,
        )
        self.index = column_list_item.column.position - 1
        self.app.needs_refresh = True

    def send_error_notify(self, column_name: str):
        self.notify(
            title="Column not empty",
            message=f"Remove all tasks in column [blue]{column_name}[/] before deletion",
            timeout=1,
            severity="error",
        )

    async def update_columns(self):
        self.app.update_column_list()
        await self.clear()
        await self.extend(
            [FirstListItem()]
            + [ColumnListItem(column=column) for column in self.app.column_list]
        )

    async def update_dependent_widgets(self):
        await self.app.screen.query_one(StatusColumnSelector).recompose()
        self.app.screen.query_one(StatusColumnSelector).get_select_widget_values()
        await self.app.screen.query_one(BoardColumnsInView).recompose()

    def watch_amount_visible(self):
        self.border_title = f"columns.visible  [cyan]{self.amount_visible} / {len(self.app.column_list)}[/]"

    @on(ListView.Selected)
    def on_space_key(self, event: ListView.Selected):
        if isinstance(event.item, FirstListItem):
            self.action_addrule_press()
        else:
            self.change_column_visibility(event.item)

    def change_column_visibility(self, column_list_item: ColumnListItem):
        column_list_item.column_visible = not column_list_item.column_visible
        self.amount_visible += 1 if column_list_item.column_visible else -1

        self.app.backend.update_column_visibility(
            column_id=column_list_item.column.column_id,
            visible=column_list_item.column_visible,
        )
        self.app.update_column_list()
        self.app.needs_refresh = True

    async def move_column_position(
        self, column_list_item: ColumnListItem, direction: Literal["up", "down"]
    ):
        modifier = 1 if direction == "down" else -1
        old_position = column_list_item.column.position
        new_position = old_position + modifier
        other_column_id = self.children[new_position].column.column_id
        # Update New Position
        switch_column_positions_db(
            current_column_id=column_list_item.column.column_id,
            other_column_id=other_column_id,
            old_position=old_position,
            new_position=new_position,
            database=self.app.config.backend.sqlite_settings.database_path,
        )
        # Update state and Widgets
        await self.update_columns()
        await self.update_dependent_widgets()
        # Trigger Update on tab Switch
        self.app.needs_refresh = True
        self.index = new_position
        self.focus()

    @on(ColumnListItem.Triggered)
    async def handle_button_events(self, event: ColumnListItem.Triggered):
        match event.interaction:
            case "del":
                self.delete_column(event.column_list_item)
            case "vis":
                self.change_column_visibility(event.column_list_item)
            case "rename":
                self.rename_column(event.column_list_item)
            case "up":
                await self.move_column_position(
                    column_list_item=event.column_list_item, direction="up"
                )
            case "down":
                await self.move_column_position(
                    column_list_item=event.column_list_item, direction="down"
                )
            case _:
                return


class StatusColumnSelector(Vertical):
    app: "KanbanTui"
    """Widget to select the columns, which are used to update the start/finish dates on tasks"""

    async def on_mount(self):
        self.border_title = "column.status_update"
        with self.prevent(Select.Changed):
            yield self.get_select_widget_values()

    def compose(self) -> Iterable[Widget]:
        with Horizontal(classes="setting-horizontal"):
            reset_label = Label("Reset")
            reset_label.tooltip = """Placing a task in this column resets its [green]start_date[/] and [green]finish_date[/]"""
            yield reset_label
            reset_select = VimSelect(
                [
                    (Text.from_markup(column.name), column.column_id)
                    for column in self.app.column_list
                ],
                value=self.app.active_board.reset_column or Select.BLANK,
                prompt="No reset column",
                id="select_reset",
            )
            reset_select.jump_mode = "focus"
            yield reset_select
        with Horizontal(classes="setting-horizontal"):
            start_label = Label("Start")
            start_label.tooltip = """Placing a task in this column starts the task and updates the [green]start_date[/] of the task"""
            yield start_label
            yield VimSelect(
                [
                    (Text.from_markup(column.name), column.column_id)
                    for column in self.app.column_list
                ],
                value=self.app.active_board.start_column or Select.BLANK,
                prompt="No start column",
                id="select_start",
            )
        with Horizontal(classes="setting-horizontal"):
            finish_label = Label("Finish")
            finish_label.tooltip = """Placing a task in this column finishes the task if it was started and updates the [green]finish_date[/] of the task"""
            yield finish_label
            yield VimSelect(
                [
                    (Text.from_markup(column.name), column.column_id)
                    for column in self.app.column_list
                ],
                value=self.app.active_board.finish_column or Select.BLANK,
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

    async def get_select_widget_values(self):
        # Get valid column IDs
        valid_column_ids = yield {col.column_id for col in self.app.column_list}

        if self.app.active_board.reset_column is not None:
            # Only set if the column still exists
            if self.app.active_board.reset_column in valid_column_ids:
                self.query_exactly_one(
                    "#select_reset", Select
                ).value = self.app.active_board.reset_column

        if self.app.active_board.start_column is not None:
            # Only set if the column still exists
            if self.app.active_board.start_column in valid_column_ids:
                self.query_exactly_one(
                    "#select_start", Select
                ).value = self.app.active_board.start_column

        if self.app.active_board.finish_column is not None:
            # Only set if the column still exists
            if self.app.active_board.finish_column in valid_column_ids:
                self.query_exactly_one(
                    "#select_finish", Select
                ).value = self.app.active_board.finish_column


class SettingsView(Vertical):
    app: "KanbanTui"

    def compose(self) -> Iterable[Widget]:
        yield DataBasePathInput(classes="setting-block")
        with Horizontal(classes="setting-horizontal"):
            yield TaskAlwaysExpandedSwitch(classes="setting-block")
            yield TaskMovementSelector(classes="setting-block")
        with Horizontal(classes="setting-horizontal"):
            yield TaskDefaultColorSelector(classes="setting-block")
            yield BoardColumnsInView(classes="setting-block")
        with Horizontal(classes="setting-horizontal"):
            yield StatusColumnSelector(classes="setting-block")
            yield ColumnSelector(classes="setting-block")
