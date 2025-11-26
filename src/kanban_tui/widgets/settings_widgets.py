from __future__ import annotations
from typing import Iterable, TYPE_CHECKING


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
    delete_column_db,
    update_single_column_position_db,
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

    def compose(self) -> Iterable[Widget]:
        yield Label("Columns in view")
        with self.prevent(Select.Changed):
            column_select = VimSelect.from_values(
                [i + 1 for i in range(len(self.app.column_list))],
                value=self.app.config.board.columns_in_view,
                id="select_columns_in_view",
                allow_blank=False,
            )
            column_select.jump_mode = "focus"
            yield column_select

    @on(Select.Changed)
    def update_config(self, event: Select.Changed):
        self.app.config.set_columns_in_view(event.select.value)


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
                classes="shown" if self.column.visible else None,
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

    @on(Button.Pressed)
    def trigger_column_delete(self, event: Button.Pressed):
        if "del" in event.button.id:
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
    jump_mode = "focus"

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
        self.border_title = "column.visibility"
        self.amount_visible = len(self.app.visible_column_dict)

    def __init__(self, *args, **kwargs) -> None:
        children = [FirstListItem()] + [
            ColumnListItem(column=column) for column in self.app.column_list
        ]
        super().__init__(*children, id="column_list", initial_index=0, *args, **kwargs)

    # rename Column
    @work()
    async def action_rename_column(self):
        if not isinstance(self.highlighted_child, ColumnListItem):
            return

        event_col_name = await self.app.push_screen(
            ModalUpdateColumnScreen(column=self.highlighted_child.column),
            wait_for_dismiss=True,
        )
        if event_col_name:
            column, new_name = event_col_name
            self.app.backend.update_column_name(
                column_id=column.column_id,
                new_name=new_name,
            )

            # Update state and Widgets
            self.app.update_column_list()
            await self.clear()
            await self.extend(
                [FirstListItem()]
                + [ColumnListItem(column=column) for column in self.app.column_list]
            )
            await self.app.screen.query_one(StatusColumnSelector).recompose()
            self.app.screen.query_one(StatusColumnSelector).get_select_widget_values()

            self.app.needs_refresh = True

            self.index = column.position

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
                self.app.backend.create_new_column(
                    board_id=self.app.active_board.board_id,
                    position=event.addrule.position + 1,
                    name=column_name,
                )
                self.app.update_column_list()
                await self.clear()
                await self.extend(
                    [FirstListItem()]
                    + [ColumnListItem(column=column) for column in self.app.column_list]
                )
                # Update dependent Widgets
                await self.app.screen.query_one(BoardColumnsInView).recompose()
                await self.app.screen.query_one(StatusColumnSelector).recompose()
                self.app.screen.query_one(
                    StatusColumnSelector
                ).get_select_widget_values()
                self.index = event.addrule.position + 1
                self.amount_visible += 1

        self.app.push_screen(
            ModalUpdateColumnScreen(event=event), callback=modal_add_new_column
        )

    # Delete Column
    def action_delete_press(self):
        if isinstance(self.highlighted_child, ColumnListItem):
            column_id = self.highlighted_child.column.column_id
            target_button_id = f"#button_col_del_{column_id}"
            self.highlighted_child.query_one(target_button_id, Button).press()

    @on(ColumnListItem.Deleted)
    @work()
    async def delete_column(self, event: ColumnListItem.Deleted):
        column = event.column_list_item.column
        if (
            len(
                [task for task in self.app.task_list if task.column == column.column_id]
            )
            != 0
        ):
            self.send_error_notify(column.name)
            return

        confirm_deletion = await self.app.push_screen(
            ModalConfirmScreen(text=f"Delete Column [blue]{column.name}[/]"),
            wait_for_dismiss=True,
        )
        if not confirm_deletion:
            return

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
        # Update dependent Widgets
        await self.app.screen.query_one(StatusColumnSelector).recompose()
        self.app.screen.query_one(StatusColumnSelector).get_select_widget_values()
        await self.app.screen.query_one(BoardColumnsInView).recompose()

        self.notify(
            title="Columns Updated",
            message=f"Column [blue]{column_name}[/] deleted",
            timeout=2,
        )

    def send_error_notify(self, column_name: str):
        self.notify(
            title="Column not empty",
            message=f"Remove all tasks in column [blue]{column_name}[/] before deletion",
            timeout=1,
            severity="error",
        )

    def watch_amount_visible(self):
        self.border_title = f"columns.visible  [cyan]{self.amount_visible} / {len(self.app.column_list)}[/]"

    @on(ListView.Selected)
    def on_space_key(self, event: ListView.Selected):
        if isinstance(event.list_view.highlighted_child, FirstListItem):
            self.action_addrule_press()
        else:
            if event.list_view.highlighted_child:
                column_id = self.highlighted_child.column.column_id
                target_button_id = f"#button_col_vis_{column_id}"
                event.list_view.highlighted_child.query_one(
                    target_button_id, Button
                ).press()

    @on(Button.Pressed)
    async def handle_button_events(self, event: Button.Pressed):
        button_kind = event.button.id.split("_")[2]
        column_id = int(event.button.id.split("_")[-1])
        match button_kind:
            case "vis":
                event.button.toggle_class("shown")

                column_is_visible = event.button.has_class("shown")
                self.amount_visible += 1 if column_is_visible else -1

                self.app.backend.update_column_visibility(
                    column_id=column_id,
                    visible=column_is_visible,
                )
                self.app.update_column_list()
                self.app.needs_refresh = True
            case "rename":
                self.action_rename_column()
            case "up":
                new_position = event.button.parent.parent.parent.column.position - 1
                old_position = event.button.parent.parent.parent.column.position
                # Update New Position
                update_single_column_position_db(
                    column_id=column_id,
                    new_position=new_position,
                    database=self.app.config.backend.sqlite_settings.database_path,
                )
                # Update Place other column to old position
                other_column_id = self.children[new_position].column.column_id
                update_single_column_position_db(
                    column_id=other_column_id,
                    new_position=old_position,
                    database=self.app.config.backend.sqlite_settings.database_path,
                )

                # Update state and Widgets
                self.app.update_column_list()
                await self.clear()
                await self.extend(
                    [FirstListItem()]
                    + [ColumnListItem(column=column) for column in self.app.column_list]
                )
                # Trigger Update on tab Switch
                self.app.needs_refresh = True
                self.index = new_position
                self.focus()

            case "down":
                new_position = event.button.parent.parent.parent.column.position + 1
                old_position = event.button.parent.parent.parent.column.position
                # Update New Position
                update_single_column_position_db(
                    column_id=column_id,
                    new_position=new_position,
                    database=self.app.config.backend.sqlite_settings.database_path,
                )
                # Update Place other column to old position
                other_column_id = self.children[new_position].column.column_id
                update_single_column_position_db(
                    column_id=other_column_id,
                    new_position=old_position,
                    database=self.app.config.backend.sqlite_settings.database_path,
                )

                # Update state and Widgets
                self.app.update_column_list()
                await self.clear()
                await self.extend(
                    [FirstListItem()]
                    + [ColumnListItem(column=column) for column in self.app.column_list]
                )
                # Trigger Update on tab Switch
                self.app.needs_refresh = True
                self.index = new_position
                self.focus()
            case _:
                return


class StatusColumnSelector(Vertical):
    app: "KanbanTui"
    """Widget to select the columns, which are used to update the start/finish dates on tasks"""

    def on_mount(self):
        self.border_title = "column.status_update"
        with self.prevent(Select.Changed):
            self.get_select_widget_values()

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
                # value=self.app.active_board.reset_column or BLANK,
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
                # value=self.app.active_board.start_column or BLANK,
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
