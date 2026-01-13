from textual.widgets import Button, Input
from kanban_tui.app import KanbanTui
from kanban_tui.modal.modal_category_screen import (
    ModalCategoryManageScreen,
    ModalNewCategoryScreen,
    CategoryList,
)
from kanban_tui.modal.modal_confirm_screen import ModalConfirmScreen

APP_SIZE = (150, 50)


async def test_modal_category_manage_display(test_app: KanbanTui):
    """Test that the category management screen displays existing categories."""
    async with test_app.run_test(size=APP_SIZE) as pilot:
        # Push the screen directly
        screen = ModalCategoryManageScreen(current_category_id=None)
        await pilot.app.push_screen(screen)

        assert isinstance(pilot.app.screen, ModalCategoryManageScreen)

        category_list = pilot.app.screen.query_one(CategoryList)
        assert (
            len(category_list.children) == 3
        )  # red, green, blue from test_app fixture

        # Check if "New Category" button is present
        assert pilot.app.screen.query_one("#btn_create_category", Button)


async def test_modal_category_create_new(test_app: KanbanTui):
    """Test creating a new category."""
    async with test_app.run_test(size=APP_SIZE) as pilot:
        screen = ModalCategoryManageScreen(current_category_id=None)
        await pilot.app.push_screen(screen)

        # Click "New Category"
        await pilot.click("#btn_create_category")

        assert isinstance(pilot.app.screen, ModalNewCategoryScreen)

        assert pilot.app.screen.query_one("#btn_continue_new_category", Button).disabled

        # Enter Name
        await pilot.click("#input_category_name")
        await pilot.press(*"Test Category")

        # Enter Color
        await pilot.click("#input_category_color")
        await pilot.press(*"cyan")

        # Button should be enabled now
        assert not pilot.app.screen.query_one(
            "#btn_continue_new_category", Button
        ).disabled

        # Click Create
        await pilot.click("#btn_continue_new_category")

        # Should return to Manage Screen
        assert isinstance(pilot.app.screen, ModalCategoryManageScreen)

        # Check if new category is in list
        category_list = pilot.app.screen.query_one(CategoryList)
        assert len(category_list.children) == 4

        # Verify backend
        categories = pilot.app.backend.get_all_categories()
        assert len(categories) == 4
        assert categories[-1].name == "Test Category"
        assert categories[-1].color == "cyan"


async def test_modal_category_edit(test_app: KanbanTui):
    """Test editing an existing category."""
    async with test_app.run_test(size=APP_SIZE) as pilot:
        screen = ModalCategoryManageScreen(current_category_id=None)
        await pilot.app.push_screen(screen)

        # Select first category (red)
        category_list = pilot.app.screen.query_one(CategoryList)
        category_list.index = 0

        # Press 'e' to edit
        await pilot.press("e")

        assert isinstance(pilot.app.screen, ModalNewCategoryScreen)

        # Check values populated
        assert pilot.app.screen.query_one("#input_category_name", Input).value == "red"

        # Change Name
        await pilot.click("#input_category_name")
        # Input.value setting directly is easier for test state reset if select_all is tricky
        pilot.app.screen.query_one("#input_category_name", Input).value = ""
        await pilot.press(*"Dark Red")

        # Click Continue
        await pilot.click("#btn_continue_new_category")

        # Should return to Manage Screen
        assert isinstance(pilot.app.screen, ModalCategoryManageScreen)

        # Verify backend
        categories = pilot.app.backend.get_all_categories()
        assert categories[0].name == "Dark Red"


async def test_modal_category_delete(test_app: KanbanTui):
    """Test deleting a category."""
    async with test_app.run_test(size=APP_SIZE) as pilot:
        screen = ModalCategoryManageScreen(current_category_id=None)
        await pilot.app.push_screen(screen)

        # Select first category
        category_list = pilot.app.screen.query_one(CategoryList)
        category_list.index = 0

        # Press 'd' to delete
        await pilot.press("d")

        assert isinstance(pilot.app.screen, ModalConfirmScreen)

        # Confirm
        await pilot.click("#btn_continue_delete")

        # Should return to Manage Screen
        assert isinstance(pilot.app.screen, ModalCategoryManageScreen)

        # Verify list updated
        category_list = pilot.app.screen.query_one(CategoryList)
        assert len(category_list.children) == 2

        # Verify backend
        categories = pilot.app.backend.get_all_categories()
        assert len(categories) == 2
        assert "red" not in [c.name for c in categories]


async def test_modal_category_create_validation_invalid_color(test_app: KanbanTui):
    """Test validation for invalid color."""
    async with test_app.run_test(size=APP_SIZE) as pilot:
        screen = ModalCategoryManageScreen(current_category_id=None)
        await pilot.app.push_screen(screen)

        await pilot.click("#btn_create_category")

        # Enter Name
        await pilot.click("#input_category_name")
        await pilot.press(*"Bad Color Category")

        # Enter Invalid Color
        await pilot.click("#input_category_color")
        await pilot.press(*"notacolor")

        # Button should be disabled
        assert pilot.app.screen.query_one("#btn_continue_new_category", Button).disabled

        # Input should have invalid class (or logic check)
        color_input = pilot.app.screen.query_one("#input_category_color", Input)
        assert not color_input.is_valid


async def test_modal_category_selection(test_app: KanbanTui):
    """Test selecting a category returns it (dismisses screen)."""
    async with test_app.run_test(size=APP_SIZE) as pilot:
        screen = ModalCategoryManageScreen(current_category_id=None)
        await pilot.app.push_screen(screen)

        # Select second category (green)
        category_list = pilot.app.screen.query_one(CategoryList)
        category_list.index = 1

        # Simulate pressing enter/selecting
        await pilot.press("enter")

        # Check screen dismissed
        assert not isinstance(pilot.app.screen, ModalCategoryManageScreen)


async def test_modal_category_cancel_create(test_app: KanbanTui):
    """Test cancelling creation."""
    async with test_app.run_test(size=APP_SIZE) as pilot:
        screen = ModalCategoryManageScreen(current_category_id=None)
        await pilot.app.push_screen(screen)

        await pilot.click("#btn_create_category")
        assert isinstance(pilot.app.screen, ModalNewCategoryScreen)

        await pilot.click("#btn_cancel_new_category")

        assert isinstance(pilot.app.screen, ModalCategoryManageScreen)
        assert len(pilot.app.backend.get_all_categories()) == 3
