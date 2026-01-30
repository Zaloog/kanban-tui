from click.testing import CliRunner

from kanban_tui.cli import cli
from kanban_tui.config import Backends
from kanban_tui.utils import CATEGORY_COLOR_POOL

CATEGORY_OUTPUT = """Category(category_id=1, name='red', color='#FF0000')
Category(category_id=2, name='green', color='#00FF00')
Category(category_id=3, name='blue', color='#0000FF')
"""

CATEGORY_OUTPUT_JSON = """[
    {
        "category_id": 1,
        "name": "red",
        "color": "#FF0000"
    },
    {
        "category_id": 2,
        "name": "green",
        "color": "#00FF00"
    },
    {
        "category_id": 3,
        "name": "blue",
        "color": "#0000FF"
    }
]
"""


def test_category_wrong_backend(test_app, test_jira_config):
    test_app.config.backend.mode = Backends.JIRA
    test_app.backend = test_app.get_backend()

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["category", "list"], obj=test_app)
        assert result.exit_code == 2
        assert (
            f"Currently using `{test_app.config.backend.mode}` backend."
            in result.output
        )
        assert (
            f"Please change the backend to `{Backends.SQLITE}` before using the `category` command."
            in result.output
        )


def test_category_list(test_app):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["category", "list"], obj=test_app)
        assert result.exit_code == 0
        assert result.output == CATEGORY_OUTPUT


def test_category_list_json(test_app):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["category", "list", "--json"], obj=test_app)
        assert result.exit_code == 0
        assert result.output == CATEGORY_OUTPUT_JSON


def test_category_list_no_categories(no_task_app):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["category", "list"], obj=no_task_app)
        assert result.exit_code == 0
        assert result.output == "No categories created yet.\n"


def test_category_create(test_app):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            args=["category", "create", "yellow", "#FFFF00"],
            obj=test_app,
        )
        assert result.exit_code == 0
        assert "Created category `yellow`" in result.output

        # Verify category was created
        categories = test_app.backend.get_all_categories()
        assert len(categories) == 4
        assert categories[3].name == "yellow"
        assert categories[3].color == "#FFFF00"


def test_category_delete(test_app):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            args=["category", "delete", "3", "--no-confirm"],
            obj=test_app,
        )
        assert result.exit_code == 0
        assert result.output == "Deleted category with category_id = 3.\n"

        # Verify category was deleted
        categories = test_app.backend.get_all_categories()
        assert len(categories) == 2
        assert all(cat.category_id != 3 for cat in categories)


def test_category_delete_with_confirm(test_app):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            args=["category", "delete", "2"],
            obj=test_app,
            input="y\n",
        )
        assert result.exit_code == 0
        assert "Deleted category with category_id = 2." in result.output

        # Verify category was deleted
        categories = test_app.backend.get_all_categories()
        assert len(categories) == 2
        assert all(cat.category_id != 2 for cat in categories)


def test_category_delete_nonexistent(test_app):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            args=["category", "delete", "999", "--no-confirm"],
            obj=test_app,
        )
        assert result.exit_code == 0
        assert "There is no category with category_id = 999" in result.output


def test_category_delete_no_categories(no_task_app):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            args=["category", "delete", "1", "--no-confirm"],
            obj=no_task_app,
        )
        assert result.exit_code == 0
        assert "No categories created yet." in result.output


def test_category_create_optional_color(test_app):
    """Test creating a category without providing a color."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Get existing colors to verify prefill logic
        existing_categories = test_app.backend.get_all_categories()
        used_colors = [cat.color for cat in existing_categories]

        result = runner.invoke(
            cli,
            args=["category", "create", "New Auto Color"],
            obj=test_app,
        )
        assert result.exit_code == 0
        assert "Created category `New Auto Color` with color" in result.output

        # Verify category was created with a valid color
        categories = test_app.backend.get_all_categories()
        assert len(categories) == 4
        new_cat = categories[3]
        assert new_cat.name == "New Auto Color"
        assert new_cat.color not in used_colors
        assert new_cat.color in CATEGORY_COLOR_POOL


def test_category_create_invalid_color(test_app):
    """Test creating a category with an invalid color."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            args=["category", "create", "Invalid Color", "notacolor"],
            obj=test_app,
        )
        assert result.exit_code == 0
        assert "Invalid color: notacolor" in result.output

        # Verify category was NOT created
        categories = test_app.backend.get_all_categories()
        assert len(categories) == 3


def test_category_update_name_only(test_app):
    """Test updating only the category name."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            args=["category", "update", "1", "--name", "Updated Red"],
            obj=test_app,
        )
        assert result.exit_code == 0
        assert "Updated category with category_id = 1" in result.output

        # Verify update
        cat = test_app.backend.get_category_by_id(1)
        assert cat.name == "Updated Red"
        assert cat.color == "#FF0000"  # Original color


def test_category_update_color_only(test_app):
    """Test updating only the category color."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            args=["category", "update", "2", "--color", "cyan"],
            obj=test_app,
        )
        assert result.exit_code == 0
        assert "Updated category with category_id = 2" in result.output

        # Verify update
        cat = test_app.backend.get_category_by_id(2)
        assert cat.name == "green"  # Original name
        assert cat.color == "cyan"


def test_category_update_both(test_app):
    """Test updating both name and color."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            args=[
                "category",
                "update",
                "3",
                "--name",
                "Blue Updated",
                "--color",
                "magenta",
            ],
            obj=test_app,
        )
        assert result.exit_code == 0
        assert "Updated category with category_id = 3" in result.output

        # Verify update
        cat = test_app.backend.get_category_by_id(3)
        assert cat.name == "Blue Updated"
        assert cat.color == "magenta"


def test_category_update_invalid_color(test_app):
    """Test updating with an invalid color."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            args=["category", "update", "1", "--color", "invalid-color"],
            obj=test_app,
        )
        assert result.exit_code == 0
        assert "Invalid color: invalid-color" in result.output

        # Verify NO update
        cat = test_app.backend.get_category_by_id(1)
        assert cat.color == "#FF0000"


def test_category_update_nonexistent(test_app):
    """Test updating a non-existent category."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            args=["category", "update", "999", "--name", "Nope"],
            obj=test_app,
        )
        assert result.exit_code == 0
        assert "There is no category with category_id = 999" in result.output
