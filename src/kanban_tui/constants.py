from pathlib import Path

from xdg_base_dirs import xdg_config_home
from platformdirs import user_config_path, user_data_path, user_runtime_path


DEFAULT_COLUMN_DICT = {"Ready": True, "Doing": True, "Done": True, "Archive": False}

DB_NAME = "database.db"
CONFIG_NAME = "kanban_tui.yaml"

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


def _create_kanban_tui_dirs(root: Path) -> Path:
    directory = root / "kanban_tui"
    directory.mkdir(exist_ok=True, parents=True)
    return directory


CONFIG_DIR = _create_kanban_tui_dirs(xdg_config_home())
CONFIG_FILE = CONFIG_DIR / "config.toml"
