from __future__ import annotations
from typing import Iterable, TYPE_CHECKING

from rich.text import Text

from kanban_tui.classes.category import Category

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui

from textual import on
from textual.binding import Binding
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import (
    Input,
    Button,
    Label,
    ListView,
    Footer,
    ListItem,
    Rule,
)
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen

# https://github.com/1dancook/tailwind-color-picker/blob/master/src/tailwind_cp/main.py#L20-L43


class ModalCategoryManageScreen(ModalScreen):
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Close"),
    ]

    app: "KanbanTui"
    color: reactive[str] = reactive("transparent")

    def compose(self) -> Iterable[Widget]:
        with Vertical():
            yield Label("Your Boards", id="label_header")
            yield CategoryList()
            yield Button(
                "New Board",
                id="btn_create_board",
                variant="success",
            )

            yield Footer(show_command_palette=False)


class CategoryList(ListView):
    app: "KanbanTui"

    BINDINGS = [
        Binding(key="j", action="cursor_down", show=False),
        Binding(key="k", action="cursor_up", show=False),
    ]

    def __init__(self) -> None:
        board_listitems = self.get_category_list_items()
        super().__init__(*board_listitems, id="category_list")

    async def populate_widget(self, index: int | None = None):
        await self.clear()
        category_listitems = self.get_category_list_items()
        await self.extend(category_listitems)
        self.index = index
        self.refresh_bindings()

    def get_category_list_items(self) -> list[CategoryListItem]:
        return [
            CategoryListItem(category)
            for category in self.app.backend.get_all_categories()
        ]

    def on_mount(self):
        self.focus()


class CategoryListItem(ListItem):
    app: "KanbanTui"

    def __init__(self, category: Category) -> None:
        self.category = category
        super().__init__(id=f"listitem_category_{self.category.category_id}")

    def compose(self) -> Iterable[Widget]:
        self.styles.background = "green"
        with Horizontal():
            yield Label(Text.from_markup(self.category.name))
            yield Rule(orientation="vertical")
            yield Label(f"{self.category.color}")

    @on(Button.Pressed, "#btn_confirm_category")
    def create_new_category(self):
        self.dismiss(result=(self.query_one(Input).value, self.color))

    @on(Button.Pressed, "#btn_cancel_category")
    def cancel_new_category(self):
        self.dismiss(result=None)
