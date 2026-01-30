from click.testing import CliRunner

from kanban_tui.cli import cli
from kanban_tui.config import Backends

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
        assert result.output == "Created category `yellow` with category_id = 4.\n"

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
