from dataclasses import dataclass
from typing import Iterable, TYPE_CHECKING

from textual.coordinate import Coordinate

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui

from rich.text import Text
from textual import on
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Input, Button, Label, DataTable
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen

# https://github.com/1dancook/tailwind-color-picker/blob/master/src/tailwind_cp/main.py#L20-L43
COLORS = [
    (
        "#d6d3d1",
        "#a8a29e",
        "#78716c",
        "#57534e",
        "#44403c",
        "#292524",
        "#1c1917",
        "#0c0a09",
    ),
    (
        "#fca5a5",
        "#f87171",
        "#ef4444",
        "#dc2626",
        "#b91c1c",
        "#991b1b",
        "#7f1d1d",
        "#450a0a",
    ),
    (
        "#fdba74",
        "#fb923c",
        "#f97316",
        "#ea580c",
        "#c2410c",
        "#9a3412",
        "#7c2d12",
        "#431407",
    ),
    (
        "#fcd34d",
        "#fbbf24",
        "#f59e0b",
        "#d97706",
        "#b45309",
        "#92400e",
        "#78350f",
        "#451a03",
    ),
    (
        "#fde047",
        "#facc15",
        "#eab308",
        "#ca8a04",
        "#a16207",
        "#854d0e",
        "#713f12",
        "#422006",
    ),
    (
        "#bef264",
        "#a3e635",
        "#84cc16",
        "#65a30d",
        "#4d7c0f",
        "#3f6212",
        "#365314",
        "#1a2e05",
    ),
    (
        "#86efac",
        "#4ade80",
        "#22c55e",
        "#16a34a",
        "#15803d",
        "#166534",
        "#14532d",
        "#052e16",
    ),
    (
        "#6ee7b7",
        "#34d399",
        "#10b981",
        "#059669",
        "#047857",
        "#065f46",
        "#064e3b",
        "#022c22",
    ),
    (
        "#5eead4",
        "#2dd4bf",
        "#14b8a6",
        "#0d9488",
        "#0f766e",
        "#115e59",
        "#134e4a",
        "#042f2e",
    ),
    (
        "#67e8f9",
        "#22d3ee",
        "#06b6d4",
        "#0891b2",
        "#0e7490",
        "#155e75",
        "#164e63",
        "#083344",
    ),
    (
        "#7dd3fc",
        "#38bdf8",
        "#0ea5e9",
        "#0284c7",
        "#0369a1",
        "#075985",
        "#0c4a6e",
        "#082f49",
    ),
    (
        "#93c5fd",
        "#60a5fa",
        "#3b82f6",
        "#2563eb",
        "#1d4ed8",
        "#1e40af",
        "#1e3a8a",
        "#172554",
    ),
    (
        "#a5b4fc",
        "#818cf8",
        "#6366f1",
        "#4f46e5",
        "#4338ca",
        "#3730a3",
        "#312e81",
        "#1e1b4b",
    ),
    (
        "#c4b5fd",
        "#a78bfa",
        "#8b5cf6",
        "#7c3aed",
        "#6d28d9",
        "#5b21b6",
        "#4c1d95",
        "#2e1065",
    ),
    (
        "#d8b4fe",
        "#c084fc",
        "#a855f7",
        "#9333ea",
        "#7e22ce",
        "#6b21a8",
        "#581c87",
        "#3b0764",
    ),
    (
        "#f0abfc",
        "#e879f9",
        "#d946ef",
        "#c026d3",
        "#a21caf",
        "#86198f",
        "#701a75",
        "#4a044e",
    ),
    (
        "#f9a8d4",
        "#f472b6",
        "#ec4899",
        "#db2777",
        "#be185d",
        "#9d174d",
        "#831843",
        "#500724",
    ),
    (
        "#fda4af",
        "#fb7185",
        "#f43f5e",
        "#e11d48",
        "#be123c",
        "#9f1239",
        "#881337",
        "#4c0519",
    ),
]


class CategoryColorPicker(ModalScreen):
    app: "KanbanTui"
    color: reactive[str] = reactive("transparent")

    def compose(self) -> Iterable[Widget]:
        with Vertical():
            yield TitleInput(placeholder="Enter Category Name")
            yield Label("Pick your Category Color")
            yield ColorTable()
            with Horizontal(id="horizontal_buttons"):
                yield Button(
                    "Add Category", id="btn_confirm_category", variant="success"
                )
                yield Button("Go Back", id="btn_cancel_category", variant="error")
        return super().compose()

    @on(Button.Pressed, "#btn_confirm_category")
    def create_new_category(self):
        self.dismiss(result=(self.query_one(TitleInput).value, self.color))

    @on(Button.Pressed, "#btn_cancel_category")
    def cancel_new_category(self):
        self.dismiss(result=None)

    @on(DataTable.CellHighlighted)
    def update_input_background(self, event: DataTable.CellHighlighted):
        self.color = event.data_table.get_cell_at(event.coordinate).color_value

    def watch_color(self):
        self.query_one(TitleInput).background = self.color


class TitleInput(Input):
    background: reactive[str] = reactive("black", recompose=True)

    def watch_background(self):
        self.set_styles(f"background:{self.background};")


@dataclass
class ColorCell:
    """
    A dataclass to hold the value of a color.

    As a rich renderable, it will display as a block
    using it's color for the background.
    """

    color_value: str  # hex color starting with hash
    text: str = " " * 5

    def __rich__(self):
        # A block of CELL_WIDTH spaces wide, using it's value as the background color
        return Text(self.text, f"black on {self.color_value}")

    def __str__(self):
        return str(self.color_value)


class ColorTable(DataTable):
    BINDINGS = [
        ("j", "cursor_down", "Down"),
        ("k", "cursor_up", "Up"),
        ("h", "cursor_left", "Left"),
        ("l", "cursor_right", "Right"),
    ]

    def on_mount(self):
        self.show_header = False
        self.cell_padding = 0
        self.add_columns(*["" for x in range(len(COLORS[0]))])
        for row in COLORS:
            cells = [ColorCell(value) for value in row]
            self.add_row(
                *cells,
            )

    def watch_cursor_coordinate(
        self, old_coordinate: Coordinate, new_coordinate: Coordinate
    ) -> None:
        self.get_cell_at(old_coordinate).text = " " * 5
        self.get_cell_at(new_coordinate).text = "  x  "
        return super().watch_cursor_coordinate(old_coordinate, new_coordinate)
