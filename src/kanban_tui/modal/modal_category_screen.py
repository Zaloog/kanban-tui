from __future__ import annotations
from typing import Iterable, TYPE_CHECKING

from rich.text import Text

from kanban_tui.classes.category import Category

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui

from textual import on
from textual.binding import Binding
from textual.widget import Widget
from textual.widgets import (
    Input,
    Button,
    Label,
    ListView,
    Footer,
    ListItem,
)
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen

# https://github.com/1dancook/tailwind-color-picker/blob/master/src/tailwind_cp/main.py#L20-L43


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
        self.index = index - 1 if index else index  # ListView starts with 0
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
        with Horizontal():
            yield Label(Text.from_markup(self.category.name))
            color_label = Label(f"{self.category.color}")
            color_label.styles.background = self.category.color
            yield color_label

    @on(Button.Pressed, "#btn_confirm_category")
    def create_new_category(self):
        self.dismiss(result=(self.query_one(Input).value, self.color))

    @on(Button.Pressed, "#btn_cancel_category")
    def cancel_new_category(self):
        self.dismiss(result=None)


class ModalCategoryManageScreen(ModalScreen):
    BINDINGS = [
        Binding(key="escape", action="close_category_management", description="Close"),
        Binding(key="e", action="edit", description="Edit", show=True, priority=True),
        Binding(
            key="d", action="delete", description="Delete", show=True, priority=True
        ),
    ]

    app: "KanbanTui"

    def __init__(self, current_category_id: Category | None, *args, **kwargs) -> None:
        self.current_category_id = current_category_id
        super().__init__(*args, **kwargs)

    def compose(self) -> Iterable[Widget]:
        with Vertical():
            yield Label("Your Categories", id="label_header")
            yield CategoryList()
            yield Button(
                "New Category",
                id="btn_create_category",
                variant="success",
            )
            yield Footer(show_command_palette=False)

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action in ("edit", "delete"):
            hightlighted_item = self.query_one(CategoryList).highlighted_child
            if not hightlighted_item:
                return False
        return True

    def action_edit(self):
        hightlighted_item = self.query_one(CategoryList).highlighted_child
        if hightlighted_item:
            self.app.push_screen(
                screen=ModalNewCategoryScreen(category=hightlighted_item.category),
                callback=self.query_one(CategoryList).populate_widget,
            )

    async def action_delete(self):
        hightlighted_item = self.query_one(CategoryList).highlighted_child
        if hightlighted_item:
            category_id = hightlighted_item.category.category_id
            self.app.backend.delete_category(category_id=category_id)
            await self.query_one(CategoryList).populate_widget(index=category_id)

    def action_close_category_management(self):
        self.dismiss(self.current_category_id)

    @on(Button.Pressed)
    def create_new_category(self):
        self.app.push_screen(
            screen=ModalNewCategoryScreen(),
            callback=self.query_one(CategoryList).populate_widget,
        )

    @on(ListView.Selected, "#category_list")
    def select_category(self, event: ListView.Selected):
        if event.item:
            self.dismiss(event.item.category.category_id)


class ColorInput(Horizontal):
    def compose(self):
        yield Input(
            placeholder="Enter category color",
            validate_on=["changed"],
            id="input_category_color",
        )

    def on_mount(self):
        self.border_title = "Color"


class NameInput(Horizontal):
    def compose(self):
        yield Input(
            placeholder="e.g. textual-project",
            value="",
            id="input_category_name",
        )

    def on_mount(self):
        self.border_title = "Name"


class ModalNewCategoryScreen(ModalScreen):
    BINDINGS = [Binding("escape", "app.pop_screen", "Close")]
    app: "KanbanTui"

    def __init__(self, category: Category | None = None, *args, **kwargs) -> None:
        self.category = category
        super().__init__(*args, **kwargs)

    def compose(self) -> Iterable[Widget]:
        with Vertical():
            yield Label("Create new category", id="label_header")
            with Horizontal():
                yield NameInput(classes="input-container")
                yield ColorInput(classes="input-container")
            with Horizontal(id="horizontal_buttons_delete"):
                yield Button(
                    "Create category",
                    id="btn_continue_new_category",
                    variant="success",
                    # disabled=True,
                )
                yield Button("Cancel", id="btn_cancel_new_category", variant="error")

    def on_mount(self) -> None:
        if self.category:
            self.query_exactly_one(
                "#btn_continue_new_category", Button
            ).label = "Edit Category"
            self.query_exactly_one("#label_header", Label).update("Edit Category")
            self.query_exactly_one(
                "#input_category_name", Input
            ).value = self.category.name
            self.query_exactly_one(
                "#input_category_color", Input
            ).value = self.category.color

    @on(Button.Pressed, "#btn_continue_new_category")
    def confirm_new_category(self):
        category_name = self.query_exactly_one("#input_category_name", Input).value

        category_color = self.query_exactly_one("#input_category_color", Input).value
        if self.category:
            updated_category = self.app.backend.update_category(
                category_id=self.category.category_id,
                name=category_name,
                color=category_color,
            )
            self.dismiss(result=updated_category.category_id)
        else:
            new_category = self.app.backend.create_new_category(
                name=category_name,
                color=category_color,
            )
            self.dismiss(result=new_category.category_id)

    @on(Button.Pressed, "#btn_cancel_new_category")
    def cancel_new_category(self):
        self.dismiss(result=None)

    # TODO Add Validation of Name and Color

    # @on(Input.Changed, "#input_board_name")
    # def check_if_board_name_valid(self, event: Input.Changed):
    #     if event.validation_result is None:
    #         return
    #     self.query_exactly_one(
    #         "#btn_continue_new_board", Button
    #     ).disabled = not event.validation_result.is_valid
