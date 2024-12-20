from __future__ import annotations
from typing import Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui

from textual import on
from textual.message import Message
from textual.events import Mount, DescendantBlur
from textual.reactive import reactive
from textual.binding import Binding
from textual.widget import Widget
from textual.widgets import (
    Label,
    Switch,
    Input,
    Collapsible,
    DataTable,
    Rule,
    Button,
    ListView,
    ListItem,
)
from textual.containers import Horizontal, Vertical

from kanban_tui.modal.modal_color_pick import ColorTable, TitleInput
from kanban_tui.modal.modal_settings import ModalNewColumnScreen
from kanban_tui.modal.modal_task_screen import ModalConfirmScreen
from kanban_tui.classes.column import Column
from kanban_tui.database import (
    update_column_visibility_db,
    delete_column_db,
    create_new_column_db,
    update_column_positions_db,
)


class DataBasePathInput(Horizontal):
    app: "KanbanTui"

    def compose(self) -> Iterable[Widget]:
        self.border_title = "database.database_path"

        yield Label("Database File")
        with self.prevent(Input.Changed):
            yield Input(
                value=self.app.cfg.database_path.as_posix(),
                select_on_focus=False,
                id="input_database_path",
            )
        return super().compose()


class WorkingHoursSelector(Vertical):
    app: "KanbanTui"

    def compose(self) -> Iterable[Widget]:
        self.border_title = "kanban.settings.work_hours"

        yield Label("Working Hours (coming soon)")
        with Horizontal():
            # yield HourMinute(hour_value=self.app.cfg.work_hour_dict['start_hour'], min_value=self.app.cfg.work_hour_dict['start_min'], id="hour_minute_start")
            yield HourMinute(id="hour_minute_start")
            yield Label("to")
            # yield HourMinute(hour_value=self.app.cfg.work_hour_dict['end_hour'], min_value=self.app.cfg.work_hour_dict['end_min'], id="hour_minute_end")
            yield HourMinute(id="hour_minute_end")
        return super().compose()


class HourMinute(Horizontal):
    def __init__(
        self, hour_value: str = "00", min_value: str = "00", id: str | None = None
    ) -> None:
        self.hour_value = hour_value
        self.min_value = min_value
        super().__init__(id=id)

    def compose(self) -> Iterable[Widget]:
        with self.prevent(Input.Changed):
            yield Input(value=self.hour_value, placeholder="HH")
            # yield Input(placeholder="HH")
            yield Label(":")
            yield Input(value=self.min_value, placeholder="MM")
            # yield Input(placeholder="MM")
        return super().compose()


class AlwaysExpandedSwitch(Horizontal):
    app: "KanbanTui"

    def compose(self) -> Iterable[Widget]:
        self.border_title = "kanban.settings.tasks_always_expanded"

        yield Label("Always Expand Tasks")
        yield Switch(value=self.app.cfg.tasks_always_expanded, id="switch_expand_tasks")
        return super().compose()

    def on_switch_changed(self, event: Switch.Changed):
        self.app.cfg.set_tasks_always_expanded(new_value=event.value)


class DefaultTaskColorSelector(Horizontal):
    app: "KanbanTui"

    def _on_mount(self, event: Mount) -> None:
        self.query_one(TitleInput).value = self.app.cfg.no_category_task_color
        self.query_one(TitleInput).background = self.app.cfg.no_category_task_color
        return super()._on_mount(event)

    def compose(self) -> Iterable[Widget]:
        self.border_title = "kanban.settings.default_task_color"

        with Vertical():
            yield Label("Default Task Color")
            with self.prevent(Input.Changed):
                yield TitleInput(
                    value=self.app.cfg.no_category_task_color, id="task_color_preview"
                )
        with Collapsible(title="Pick Color"):
            with self.prevent(DataTable.CellHighlighted):
                yield ColorTable()

        return super().compose()

    @on(DataTable.CellHighlighted)
    def change_input_str_on_color_pick(self, event: DataTable.CellHighlighted):
        self.query_one(TitleInput).value = event.data_table.get_cell_at(
            event.coordinate
        ).color_value

    @on(Input.Changed)
    def update_input_color(self, event: Input.Changed):
        try:
            self.query_one(TitleInput).background = event.input.value
            self.app.cfg.set_no_category_task_color(new_color=event.input.value)
            event.input.styles.border = "tall", "green"
            event.input.border_subtitle = None
            event.input.border_title = None
        # Todo add validator to input?
        except Exception:
            event.input.styles.border = "tall", "red"
            event.input.border_subtitle = "invalid color value"
            event.input.border_title = (
                f"last valid: {self.app.cfg.no_category_task_color}"
            )

    @on(DescendantBlur)
    def reset_color(self):
        self.query_one(TitleInput).value = self.app.cfg.no_category_task_color


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

    def __init__(self, position: int, id: str | None = None) -> None:
        self.position = position
        super().__init__(id=id)

    def compose(self) -> Iterable[Widget]:
        yield Button("+")
        return super().compose()

    def on_button_pressed(self):
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
            yield Label(f"Show [blue]{self.column.name}[/]")
            yield Switch(
                value=self.column.visible,
                id=f"switch_col_vis_{self.column.column_id}",
            )
            yield Button(
                label="Delete",
                id=f"button_col_del_{self.column.column_id}",
                variant="error",
            )
        yield AddRule(position=self.column.position, id=self.column.name)

        return super().compose()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id:
            self.post_message(self.Deleted(self))


class FirstListItem(ListItem):
    app: "KanbanTui"

    def __init__(self) -> None:
        super().__init__(id="listitem_column_0")

    def compose(self) -> Iterable[Widget]:
        yield AddRule(id="first_position", position=0)

        return super().compose()


class ColumnSelector(ListView):
    app: "KanbanTui"

    BINDINGS = [
        Binding(key="j", action="cursor_down", show=False),
        Binding(key="k", action="cursor_up", show=False),
        Binding(key="enter,space", action="select_cursor", show=False),
        Binding(key="d", action="delete_press", description="Delete Column", show=True),
        Binding(
            key="n", action="addrule_press", description="Insert Column", show=True
        ),
    ]
    amount_visible: reactive[int] = reactive(0)

    def _on_mount(self, event: Mount) -> None:
        self.border_title = "column.visibility"
        self.amount_visible = len(self.app.visible_column_list)
        return super()._on_mount(event)

    def __init__(self) -> None:
        children = [FirstListItem()] + [
            ColumnListItem(column=column) for column in self.app.column_list
        ]
        super().__init__(*children, id="column_list", initial_index=None)

    # New Column
    def action_addrule_press(self):
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
                    database=self.app.cfg.database_path,
                )
                create_new_column_db(
                    board_id=self.app.active_board.board_id,
                    position=event.addrule.position + 1,
                    name=column_name,
                    visible=True,
                    database=self.app.cfg.database_path,
                )
                self.app.update_column_list()
                await self.clear()
                self.extend(
                    [FirstListItem()]
                    + [ColumnListItem(column=column) for column in self.app.column_list]
                )
                self.index = event.addrule.position + 1
                self.amount_visible += 1

                self.notify(
                    title="Columns Updated",
                    message=f"Column [blue]{column_name}[/] created",
                    timeout=2,
                )

        self.app.push_screen(
            ModalNewColumnScreen(event=event), callback=modal_add_new_column
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
            self.notify(
                title="Column not empty",
                message=f"Remove all tasks in column [blue]{column_name}[/] before deletion",
                timeout=1,
                severity="error",
            )
            return

        def modal_delete_column(event: ColumnListItem.Deleted, delete_yn: bool) -> None:
            if delete_yn:
                column_id = event.column_list_item.column.column_id
                column_name = event.column_list_item.column.name

                delete_column_db(
                    column_id=column_id, database=self.app.cfg.database_path
                )
                self.app.update_column_list()
                if event.column_list_item.column.visible:
                    self.amount_visible -= 1
                else:
                    self.watch_amount_visible()

                # Remove ListItem
                event.column_list_item.remove()

                self.notify(
                    title="Columns Updated",
                    message=f"Column [blue]{column_name}[/] deleted",
                    timeout=2,
                )

        self.app.push_screen(
            ModalConfirmScreen(text=f"Delete Column [blue]{column_name}[/]"),
            callback=lambda x: modal_delete_column(event=event, delete_yn=x),
        )

    def watch_amount_visible(self):
        self.border_title = f"columns.visible  [blue]{self.amount_visible} / {len(self.app.column_list)}[/]"

    @on(ListView.Selected)
    def on_space_key(self, event: ListView.Selected):
        if isinstance(event.list_view.highlighted_child, FirstListItem):
            self.action_addrule_press()
        else:
            event.list_view.highlighted_child.query_one(Switch).toggle()

    @on(Switch.Changed)
    def update_visibility(self, event: Switch.Changed):
        self.amount_visible += 1 if event.value else -1
        column_id = event.switch.id.split("_")[-1]
        update_column_visibility_db(
            column_id=column_id,
            visible=event.value,
            database=self.app.cfg.database_path,
        )

        self.app.update_column_list()
