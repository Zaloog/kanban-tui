from textual.containers import Horizontal
from textual.widgets import Footer, Label
from textual.widgets._footer import FooterKey

from kanban_tui.config import Backends
from kanban_tui.widgets.modal_task_widgets import VimSelect


class KanbanTuiFooter(Horizontal):
    def compose(self):
        with Horizontal():
            yield Footer(show_command_palette=False, compact=True)
        selector = VimSelect.from_values(
            values=Backends,
            allow_blank=False,
            type_to_search=False,
            compact=True,
            prompt="Backend",
            value=self.app.config.backend.mode,
        )
        selector.display = False
        yield FooterKey("C", "C", "", "show", classes="compact")
        yield Label("Backend")
        yield selector
        self.watch(selector, "expanded", callback=self.hide_label, init=False)

    def hide_label(self):
        selector_expanded = self.query_one(VimSelect).expanded
        self.query_one(Label).display = not selector_expanded
        self.query_one(VimSelect).display = selector_expanded
        self.query_one(FooterKey).display = not selector_expanded

    def toggle_show(self):
        selector = self.query_one(VimSelect)
        selector.expanded = not selector.expanded
