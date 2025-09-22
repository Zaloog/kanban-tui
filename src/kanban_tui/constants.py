from pathlib import Path

from xdg_base_dirs import xdg_config_home, xdg_data_home


DEFAULT_COLUMN_DICT = {"Ready": True, "Doing": True, "Done": True, "Archive": False}


def _create_kanban_tui_dirs(root: Path) -> Path:
    directory = root / "kanban_tui"
    directory.mkdir(exist_ok=True, parents=True)
    return directory


CONFIG_NAME = "config.toml"
CONFIG_DIR = _create_kanban_tui_dirs(xdg_config_home())
CONFIG_FILE = CONFIG_DIR / CONFIG_NAME
DEMO_CONFIG_FILE = CONFIG_DIR / "demo_config.toml"

DATABASE_NAME = "kanban_tui.db"
DATA_DIR = _create_kanban_tui_dirs(xdg_data_home())
DATABASE_FILE = DATA_DIR / DATABASE_NAME
DEMO_DATABASE_FILE = DATA_DIR / "demo_kanban_tui.db"
