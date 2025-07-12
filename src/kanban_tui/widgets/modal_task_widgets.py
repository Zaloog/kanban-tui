from datetime import datetime
from typing import Iterable, TYPE_CHECKING


if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui

from textual.reactive import reactive
from textual.events import Mount
from textual.widget import Widget
from textual.binding import Binding
from textual.widgets import TextArea, Select, Label, Switch
from textual.widgets._select import SelectOverlay
from textual.containers import Horizontal, Vertical

from kanban_tui.modal.modal_color_pick import CategoryColorPicker
from kanban_tui.widgets.date_select import CustomDateSelect


class DescriptionInfos(Vertical):
    can_focus = False

    def compose(self) -> Iterable[Widget]:
        yield TextArea()
        self.border = "$success"
        self.border_title = "Task Description"
        return super().compose()


class DetailInfos(Vertical):
    app: "KanbanTui"
    due_date: reactive[datetime] = reactive(None)

    def compose(self) -> Iterable[Widget]:
        with Horizontal(id="horizontal_category"):
            yield Label("Category:")
            yield CategorySelector()
        with Horizontal(id="horizontal_due_date"):
            yield Label("has a due Date:")
            with self.prevent(Switch.Changed):
                yield Switch(value=False, id="switch_due_date")
        yield Vertical(id="vertical_due_date_choice")

        self.border = "$success"
        self.border_title = "Additional Infos"
        return super().compose()

    def _on_mount(self, event: Mount) -> None:
        self.query_one("#vertical_due_date_choice").mount(
            Label("[yellow]??[/] days left", id="label_days_left", classes="hidden"),
            CustomDateSelect(
                placeholder="Select Due Date",
                format="YYYY-MM-DD",
                picker_mount="#vertical_modal",
                id="dateselect_due_date",
                classes="hidden",
            ),
        )
        return super()._on_mount(event)

    def on_switch_changed(self):
        if self.query_one(Switch).value:
            self.query_one(CustomDateSelect).remove_class("hidden")
            self.query_one("#label_days_left").remove_class("hidden")
        else:
            self.query_one("#label_days_left").add_class("hidden")
            self.query_one(CustomDateSelect).add_class("hidden").date = None
            self.due_date = None

    def on_date_picker_selected(self):
        self.due_date = self.query_one(CustomDateSelect).date.replace(
            microsecond=0, tzinfo=None
        )

    def watch_due_date(self):
        if not self.due_date:
            self.query_one("#label_days_left", Label).update("[yellow]??[/] days left")
            return

        # Delta Calculation
        if self.due_date.date() <= datetime.now().date():
            delta = 0
            self.query_one("#label_days_left", Label).update(
                f"[red]{delta}[/] days left"
            )
        else:
            delta = (self.due_date - datetime.now()).days + 1

        # Label display Update
        if delta == 1:
            self.query_one("#label_days_left", Label).update(
                f"[green]{delta}[/] day left"
            )
        else:
            self.query_one("#label_days_left", Label).update(
                f"[green]{delta}[/] days left"
            )


class NewCategorySelection:
    def __repr__(self) -> str:
        return "Select.NewCategory"


NEW = NewCategorySelection()


class CategorySelector(Select):
    app: "KanbanTui"
    # thanks Darren (https://github.com/darrenburns/posting/blob/main/src/posting/widgets/select.py)
    BINDINGS = [
        Binding("enter,space,l", "show_overlay", "Show Overlay", show=False),
        Binding("up,k", "cursor_up", "Cursor Up", show=False),
        Binding("down,j", "cursor_down", "Cursor Down", show=False),
    ]
    NEW = NEW

    def __init__(self):
        options = self.get_options()
        super().__init__(
            options=options,
            prompt="No Category",
            allow_blank=True,
            type_to_search=False,
        )

    def watch_value(self):
        if self.value == self.NEW:
            self.app.push_screen(CategoryColorPicker(), callback=self.jump_to_value)

    def jump_to_value(self, value: tuple[str, str] | None = None) -> None:
        if value:
            category, color = value

            self.app.cfg.add_category(category=category, color=color)
            options = self.get_options()

            self.set_options(options=options)
            self.value = category
        else:
            self.value = self.BLANK

    def get_options(self):
        options = [
            (f"[on {color}]{category}[/]", category)
            for category, color in self.app.cfg.category_color_dict.items()
        ]
        options.insert(0, ("Add a new Category", self.NEW))
        return options

    def action_cursor_up(self):
        if self.expanded:
            self.query_one(SelectOverlay).action_cursor_up()
        else:
            self.screen.focus_previous()

    def action_cursor_down(self):
        if self.expanded:
            self.query_one(SelectOverlay).action_cursor_down()
        else:
            self.screen.focus_next()


class CreationDateInfo(Horizontal):
    def compose(self) -> Iterable[Widget]:
        yield Label(
            f"Task created at: {datetime.now().replace(microsecond=0)}",
            id="label_create_date",
        )
        return super().compose()


class StartDateInfo(Vertical):
    def compose(self) -> Iterable[Widget]:
        yield Label("[red]not started yet[/]", id="label_start_date")
        self.border = "$success"
        self.border_title = "Start Date"
        return super().compose()


class FinishDateInfo(Vertical):
    def compose(self) -> Iterable[Widget]:
        yield Label("[red]not finished yet[/]", id="label_finish_date")
        self.border = "$success"
        self.border_title = "Finish Date"
        return super().compose()
