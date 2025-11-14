from textual.containers import Horizontal
from textual.widgets import Footer, Label, Select
from textual.widgets._footer import FooterKey

from kanban_tui.config import Backends
from kanban_tui.widgets.modal_task_widgets import VimSelect


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
