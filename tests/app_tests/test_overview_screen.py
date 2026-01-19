import pytest

from kanban_tui.app import KanbanTui
from kanban_tui.screens.overview_screen import OverViewScreen
from kanban_tui.widgets.overview_widgets import LogFilterButton

APP_SIZE = (150, 50)


async def test_overview_view_no_tasks(no_task_app: KanbanTui, test_database_path):
    async with no_task_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("ctrl+k")
        await pilot.pause()

        assert isinstance(pilot.app.screen, OverViewScreen)
        assert pilot.app.screen.query_one("#plot_widget").styles.width.value == 1

        await pilot.press("L")
        # 1 board CREATE + 4 column CREATEs + 3 board UPDATEs (status columns) = 8
        assert pilot.app.screen.query_one("#datatable_logs").row_count == 8


async def test_overview_view(test_app: KanbanTui, test_database_path):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("ctrl+k")
        await pilot.pause()

        assert isinstance(pilot.app.screen, OverViewScreen)
        await pilot.press("P")
        assert (
            pilot.app.screen.query_one("#tabbed_content_overview").active == "tab_plot"
        )

        await pilot.press("L")
        # 1 board + 4 columns + 3 status updates + 5 tasks = 13
        assert pilot.app.screen.query_one("#datatable_logs").row_count == 13


async def test_overview_tab_switch(test_app: KanbanTui, test_database_path):
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


async def test_overview_plot_filter_values(test_app: KanbanTui, test_database_path):
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
        (0, 3),  # Create: 1 board + 4 columns + 5 tasks = 10
        (1, 10),  # Update: 3 board status column updates = 3
        (2, 13),  # Delete: 0
        (3, 9),  # board: 1 CREATE + 3 UPDATEs = 4
        (4, 9),  # column: 4 CREATEs = 4
        (5, 8),  # task: 5 CREATEs = 5
    ],
)
async def test_overview_log_filter_values(
    test_app: KanbanTui, test_database_path, button_no, log_rows_visible
):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("ctrl+k")
        await pilot.pause()

        await pilot.press("L")
        assert pilot.app.screen.query_one("#datatable_logs").row_count == 13

        await pilot.click(
            list(pilot.app.screen.query(LogFilterButton).results())[button_no]
        )
        assert (
            pilot.app.screen.query_one("#datatable_logs").row_count == log_rows_visible
        )
