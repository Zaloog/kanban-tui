from configparser import ConfigParser
from pathlib import Path
from dataclasses import dataclass

from kanban_tui.constants import CONFIG_FULL_PATH, DB_FULL_PATH


@dataclass
class KanbanTuiConfig:
    config_path: Path = CONFIG_FULL_PATH

    def __post_init__(self):
        self.config = ConfigParser(default_section=None, allow_no_value=True)
        self.config.optionxform = str
        self.config.read(self.config_path)

    @property
    def database_path(self) -> Path:
        return Path(self.config.get(section="database", option="database_path"))

    @property
    def tasks_always_expanded(self) -> bool:
        return self.config.getboolean(
            section="kanban.settings", option="tasks_always_expanded"
        )

    @tasks_always_expanded.setter
    def tasks_always_expanded(self, new_value: bool):
        self.config.set(
            section="kanban.settings",
            option="tasks_always_expanded",
            value=f"{new_value}",
        )
        self.save()

    @property
    def show_archive(self) -> bool:
        return self.config.getboolean(section="kanban.settings", option="show_archive")

    @show_archive.setter
    def show_archive(self, new_value: bool):
        self.config.set(
            section="kanban.settings",
            option="show_archive",
            value=f"{new_value}",
        )
        self.save()

    @property
    def start_column(self) -> bool:
        return self.config.getint(section="kanban.settings", option="start_column")

    @start_column.setter
    def start_column(self, new_value: int):
        self.config.set(
            section="kanban.settings",
            option="start_column",
            value=f"{new_value}",
        )
        self.save()

    @property
    def default_task_color(self) -> bool:
        return self.config.get(
            section="kanban.settings", option="no_category_task_color"
        )

    @property
    def category_color_dict(self) -> dict:
        return self.config["category.colors"]

    def add_category(self, category: str, color: str):
        self.category_color_dict[category] = color
        self.save()

    def save(self):
        with open(self.config_path, "w") as configfile:
            self.config.write(configfile)


def init_new_config(config_path=CONFIG_FULL_PATH):
    if config_path.exists():
        return

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.touch()

    config = ConfigParser(default_section=None, allow_no_value=True)
    config.optionxform = str
    config["database"] = {"database_path": DB_FULL_PATH}
    config["category.colors"] = {}
    config["kanban.settings"] = {
        "tasks_always_expanded": False,
        "show_archive": True,
        "no_category_task_color": "gray",
        "start_column": 0,
    }

    with open(config_path, "w") as conf_file:
        config.write(conf_file)
