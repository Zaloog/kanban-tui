from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import Footer, Label, Select, Button
from textual.widgets._footer import FooterKey
from textual.widgets._select import SelectOverlay

from kanban_tui.config import Backends


class IconButton(Button): ...


class KanbanTuiFooter(Horizontal):
    def compose(self):
        with Horizontal():
            yield Footer(show_command_palette=False, compact=True)
        with self.prevent(Select.Changed):
            selector = VimSelect.from_values(
                values=Backends,
                allow_blank=False,
                type_to_search=False,
                compact=True,
                prompt="Backend",
                value=self.app.config.backend.mode,
                id="select_backend_mode",
            )
        # Keep the focus behavior
        selector.disabled = True
        selector.display = False
        yield FooterKey(
            key="C", key_display="C", description="", action="show", classes="compact"
        )
        yield Label("Backend")
        yield selector
        self.watch(selector, "expanded", callback=self.hide_label, init=False)

    def hide_label(self):
        selector = self.query_one(VimSelect)
        selector_expanded = selector.expanded
        self.query_one(Label).display = not selector_expanded
        selector.display = selector_expanded
        selector.disabled = not selector_expanded
        self.query_one(FooterKey).display = not selector_expanded

    def toggle_show(self):
        selector = self.query_one(VimSelect)
        selector.expanded = not selector.expanded


class VimSelect(Select):
    BINDINGS = [
        Binding("enter,space,l", "show_overlay", "Show Overlay", show=False),
        Binding("up,k", "cursor_up", "Cursor Up", show=False),
        Binding("down,j", "cursor_down", "Cursor Down", show=False),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._type_to_search = False

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
