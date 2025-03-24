from kanban_tui.app import KanbanTui
from kanban_tui.views.main_view import MainView

APP_SIZE = (120, 80)


async def test_overview_view_empty(empty_app: KanbanTui, test_db_full_path):
    async with empty_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("ctrl+k")
        await pilot.pause()

        assert isinstance(pilot.app.screen, MainView)
        assert pilot.app.query_one("#plot_widget").styles.width.value == 1

        # assert pilot.app.screen, MainView)


async def test_overview_view(test_app: KanbanTui, test_db_full_path):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("ctrl+k")
        await pilot.pause()

        assert isinstance(pilot.app.screen, MainView)
        await pilot.press("P")
        assert pilot.app.query_one("#tabbed_content_overview").active == "tab_plot"


async def test_overview_tab_switch(test_app: KanbanTui, test_db_full_path):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("ctrl+k")
        await pilot.pause()

        # initial is log
        assert pilot.app.query_one("#tabbed_content_overview").active == "tab_log"
        # switch to plot
        await pilot.press("P")
        assert pilot.app.query_one("#tabbed_content_overview").active == "tab_plot"
        # switch back to log
        await pilot.press("L")
        assert pilot.app.query_one("#tabbed_content_overview").active == "tab_log"


async def test_overview_plot_filter_values(test_app: KanbanTui, test_db_full_path):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("ctrl+k")
        await pilot.pause()

        await pilot.press("P")
        assert not pilot.app.query_one("#switch_plot_category_detail").value
        assert pilot.app.query_one("#select_plot_filter_amount").value == "start_date"
        assert pilot.app.query_one("#select_plot_filter_frequency").value == "month"


async def test_overview_log_filter_values(test_app: KanbanTui, test_db_full_path):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("ctrl+k")
        await pilot.pause()

        await pilot.press("L")
        # assert not pilot.app.query_one("#switch_plot_category_detail").value
        # assert pilot.app.query_one("#select_plot_filter_amount").value == "start_date"
        # assert pilot.app.query_one("#select_plot_filter_frequency").value == "month"
