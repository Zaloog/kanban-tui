from sqlite3 import Connection

from importlib.resources import files

CURRENT_SCHEMA_VERSION = 3


def read_migration_file(migration_file_name: str) -> str:
    migration_sql_str = (
        files("kanban_tui.backends.sqlite.migrations")
        .joinpath(migration_file_name)
        .read_text(encoding="utf-8")
    )
    return migration_sql_str


def apply_migration_v1_to_v2(con: Connection):
    """Migrates to v2 in version v0.13.0
    Changes:
    - Table Creation: schema_version table created
    - Table Creation: dependencies table created
    """
    sql = read_migration_file("migration_v0_13_0.sql")

    con.executescript(sql)


def apply_migration_v2_to_v3(con: Connection):
    """Migrates to v3 in version v0.14.0
    Changes:
    - Column Addition: metadata column added to tasks table
    """
    sql = read_migration_file("migration_v0_14_0.sql")

    con.executescript(sql)


def increment_schema_version(con: Connection, version: int):
    con.execute(f"INSERT INTO schema_versions VALUES ({version}, datetime('now'))")
