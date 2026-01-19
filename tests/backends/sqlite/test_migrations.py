from kanban_tui.backends.sqlite.database import get_schema_version
from kanban_tui.backends.sqlite.migrations import CURRENT_SCHEMA_VERSION


def test_migration_schema_version_latest(test_app, test_database_path):
    database_schema_version = get_schema_version(test_database_path)
    assert database_schema_version == CURRENT_SCHEMA_VERSION
