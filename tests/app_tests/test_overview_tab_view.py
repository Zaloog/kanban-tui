import pytest

from kanban_tui.app import KanbanTui
from kanban_tui.views.main_view import MainView
from kanban_tui.widgets.overview_widgets import LogFilterButton

APP_SIZE = (120, 80)


async def test_overview_view_empty(empty_app: KanbanTui, test_db_full_path):
    async with empty_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("ctrl+k")
        await pilot.pause()

        assert isinstance(pilot.app.screen, MainView)
        assert pilot.app.screen.query_one("#plot_widget").styles.width.value == 1

        await pilot.press("L")
        assert pilot.app.screen.query_one("#datatable_logs").row_count == 5

        # assert pilot.app.screen, MainView)


async def test_overview_view(test_app: KanbanTui, test_db_full_path):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("ctrl+k")
        await pilot.pause()

        assert isinstance(pilot.app.screen, MainView)
        await pilot.press("P")
        assert (
            pilot.app.screen.query_one("#tabbed_content_overview").active == "tab_plot"
        )

        await pilot.press("L")
        assert pilot.app.screen.query_one("#datatable_logs").row_count == 10


async def test_overview_tab_switch(test_app: KanbanTui, test_db_full_path):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("ctrl+k")
        await pilot.pause()

        # initial is log
        assert (
            pilot.app.screen.query_one("#tabbed_content_overview").active == "tab_log"
        )
        # switch to plot
        await pilot.press("P")
        assert (
            pilot.app.screen.query_one("#tabbed_content_overview").active == "tab_plot"
        )
        # switch back to log
        await pilot.press("L")
        assert (
            pilot.app.screen.query_one("#tabbed_content_overview").active == "tab_log"
        )


async def test_overview_plot_filter_values(test_app: KanbanTui, test_db_full_path):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("ctrl+k")
        await pilot.pause()

        await pilot.press("P")
        assert not pilot.app.screen.query_one("#switch_plot_category_detail").value
        assert (
            pilot.app.screen.query_one("#select_plot_filter_amount").value
            == "start_date"
        )
        assert (
            pilot.app.screen.query_one("#select_plot_filter_frequency").value == "month"
        )


@pytest.mark.parametrize(
    "button_no, log_rows_visible",
    [
        (0, 0),  # Create
        (1, 10),  # Update
        (2, 10),  # Delete
        (3, 9),  # board
        (4, 6),  # column
        (5, 5),  # task
    ],
)
async def test_overview_log_filter_values(
    test_app: KanbanTui, test_db_full_path, button_no, log_rows_visible
):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("ctrl+k")
        await pilot.pause()

        await pilot.press("L")
        assert pilot.app.screen.query_one("#datatable_logs").row_count == 10

        await pilot.click(
            list(pilot.app.screen.query(LogFilterButton).results())[button_no]
        )
        assert (
            pilot.app.screen.query_one("#datatable_logs").row_count == log_rows_visible
        )
