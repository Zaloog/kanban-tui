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
    def category_color_dict(self) -> dict:
        return self.config["category.colors"]

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
    config["category.colors"] = {"Work": "red", "Freetime": "green"}
    config["kanban.settings"] = {
        "tasks_always_expanded": False,
    }

    with open(config_path, "w") as conf_file:
        config.write(conf_file)
