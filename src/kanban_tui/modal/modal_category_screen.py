from __future__ import annotations
from typing import Iterable, TYPE_CHECKING

from rich.text import Text
from textual.color import Color, ColorParseError

from kanban_tui.classes.category import Category
from kanban_tui.utils import get_next_category_color

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui

from textual import on, work
from textual.binding import Binding
from textual.validation import Length, Validator, ValidationResult
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

from kanban_tui.modal.modal_confirm_screen import ModalConfirmScreen

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
        self.category: Category = category
        super().__init__(id=f"listitem_category_{self.category.category_id}")

    def compose(self) -> Iterable[Widget]:
        with Horizontal():
            yield Label(Text.from_markup(self.category.name))
            color_label = Label(f"{self.category.color}")
            color_label.styles.background = self.category.color
            yield color_label


class ModalCategoryManageScreen(ModalScreen[int | None]):
    BINDINGS = [
        Binding(key="escape", action="close_category_management", description="Close"),
        Binding(key="e", action="edit", description="Edit", show=True, priority=True),
        Binding(
            key="d", action="delete", description="Delete", show=True, priority=True
        ),
    ]

    app: "KanbanTui"

    def __init__(self, current_category_id: int | None, *args, **kwargs) -> None:
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
            if not hightlighted_item or not self.query_one(CategoryList).has_focus:
                return False
        return True

    async def action_edit(self):
        hightlighted_item = self.query_one(CategoryList).highlighted_child
        if hightlighted_item:
            await self.app.push_screen(
                screen=ModalNewCategoryScreen(category=hightlighted_item.category),
                callback=self.query_one(CategoryList).populate_widget,
            )
            self.app.needs_refresh = True

    @work()
    async def action_delete(self):
        hightlighted_item = self.query_one(CategoryList).highlighted_child

        confirm_deletion = await self.app.push_screen(
            ModalConfirmScreen("Delete category?", button_text="Delete category"),
            wait_for_dismiss=True,
        )
        if not confirm_deletion:
            return

        if hightlighted_item:
            category_id = hightlighted_item.category.category_id
            # Update current_category to not error on value update
            if self.current_category_id == category_id:
                self.current_category_id = None
            self.app.backend.delete_category(category_id=category_id)
            await self.query_one(CategoryList).populate_widget(index=category_id)
            # We need to refresh the board to update Taskcard colors
            # In case of categories being deleted/updated
            self.app.needs_refresh = True

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


class IsValidColor(Validator):
    def validate(self, value: str) -> ValidationResult:
        if self.color_can_be_parsed(value):
            return self.success()
        else:
            return self.failure(description="invalid color")

    @staticmethod
    def color_can_be_parsed(value: str) -> bool:
        try:
            Color.parse(value)
            return True
        except ColorParseError:
            return False


class ColorInputContainer(Horizontal):
    def compose(self):
        yield Input(
            placeholder="Enter category color",
            validate_on=["changed"],
            validators=[Length(minimum=1), IsValidColor()],
            valid_empty=False,
            id="input_category_color",
        )

    def on_mount(self):
        self.border_title = "Color"

    @on(Input.Changed)
    def check_validation(self, event: Input.Changed):
        if event.validation_result and event.validation_result.is_valid:
            self.remove_class("invalid")
        else:
            self.add_class("invalid")


class NameInputContainer(Horizontal):
    def compose(self):
        yield Input(
            placeholder="e.g. textual-project",
            validate_on=["changed"],
            validators=[Length(minimum=1)],
            valid_empty=False,
            id="input_category_name",
        )

    def on_mount(self):
        self.border_title = "Name"
        self.check_validation(event=Input.Changed)

    @on(Input.Changed)
    def check_validation(self, event: Input.Changed):
        if event.validation_result and event.validation_result.is_valid:
            self.remove_class("invalid")
        else:
            self.add_class("invalid")


class ModalNewCategoryScreen(ModalScreen[int | None]):
    BINDINGS = [Binding("escape", "app.pop_screen", "Close")]
    app: "KanbanTui"

    def __init__(self, category: Category | None = None, *args, **kwargs) -> None:
        self.category = category
        super().__init__(*args, **kwargs)

    def compose(self) -> Iterable[Widget]:
        with Vertical():
            yield Label("Create new category", id="label_header")
            with Horizontal():
                yield NameInputContainer(classes="input-container")
                yield ColorInputContainer(classes="input-container")
            with Horizontal(id="horizontal_buttons_delete"):
                yield Button(
                    "Create category",
                    id="btn_continue_new_category",
                    variant="success",
                    disabled=True,
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
        else:
            # Pre-fill color input with next available color from pool
            existing_categories = self.app.backend.get_all_categories()
            used_colors = [cat.color for cat in existing_categories]
            suggested_color = get_next_category_color(used_colors)
            self.query_exactly_one(
                "#input_category_color", Input
            ).value = suggested_color

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

    @on(Input.Changed)
    def check_if_all_input_fields_are_valid(self, event: Input.Changed):
        all_valid = all(
            [input.is_valid and input.value for input in self.query(Input).results()]
        )

        self.query_exactly_one(
            "#btn_continue_new_category", Button
        ).disabled = not all_valid
