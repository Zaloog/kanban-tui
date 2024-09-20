from pathlib import Path
# from platformdirs import user_config_dir, user_data_dir

COLUMNS = ["Ready", "Doing", "Done", "Archive"]

DB_NAME = "database.db"
DB_LOCATION = Path().cwd()
# DB_LOCATION = Path(
#     user_data_dir(appname="kanban-tui", appauthor=False, ensure_exists=True)
# )
DB_FULL_PATH = DB_LOCATION / DB_NAME

CONFIG_NAME = "kanban_tui.yaml"
CONFIG_LOCATION = Path().cwd()
# CONFIG_LOCATION = Path(
#     user_config_dir(appname="kanban-tui", appauthor=False, ensure_exists=True)
# )
CONFIG_FULL_PATH = CONFIG_LOCATION / CONFIG_NAME
