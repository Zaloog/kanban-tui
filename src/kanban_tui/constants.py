from platformdirs import user_config_path, user_data_path, user_runtime_path

COLUMNS = ["Ready", "Doing", "Done", "Archive"]

DB_NAME = "database.db"
CONFIG_NAME = "kanban_tui.yaml"

# For Developing
# DB_LOCATION = Path().cwd()
# CONFIG_LOCATION = Path().cwd()

# Normal Use
DB_LOCATION = user_data_path(appname="kanban-tui", appauthor=False, ensure_exists=True)
CONFIG_LOCATION = user_config_path(
    appname="kanban-tui", appauthor=False, ensure_exists=True
)

DB_FULL_PATH = DB_LOCATION / DB_NAME
CONFIG_FULL_PATH = CONFIG_LOCATION / CONFIG_NAME

# Demo
TEMP_DB_LOCATION = user_runtime_path(
    appname="kanban-tui", appauthor=False, ensure_exists=True
)
TEMP_DB_FULL_PATH = TEMP_DB_LOCATION / DB_NAME

TEMP_CONFIG_LOCATION = user_runtime_path(
    appname="kanban-tui", appauthor=False, ensure_exists=True
)
TEMP_CONFIG_FULL_PATH = TEMP_CONFIG_LOCATION / CONFIG_NAME
