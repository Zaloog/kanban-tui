from configparser import ConfigParser
from pathlib import Path

from pydantic import BaseModel, Field, ConfigDict

from kanban_tui.constants import CONFIG_FULL_PATH, DB_FULL_PATH


class KanbanTuiConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    config_path: Path = CONFIG_FULL_PATH
    config: ConfigParser = Field(default=ConfigParser(allow_no_value=True))
    tasks_always_expanded: bool = False
    no_category_task_color: str = "#004578"
    category_color_dict: dict[str | None, str] = {}
    column_dict: dict[str, bool] = {
        "Ready": True,
        "Doing": True,
        "Done": True,
        "Archive": False,
    }

    def model_post_init(self, __context):
        self.config.default_section = None
        self.config.optionxform = str
        self.config.read(self.config_path)

        self.tasks_always_expanded = self.config.getboolean(
            section="kanban.settings", option="tasks_always_expanded"
        )
        self.no_category_task_color = self.config.get(
            section="kanban.settings", option="no_category_task_color"
        )
        self.category_color_dict = self.config["category.colors"]
        self.column_dict = {
            column: True if visible == "True" else False
            for column, visible in self.config["column.visibility"].items()
        }

    @property
    def database_path(self) -> Path:
        return Path(self.config.get(section="database", option="database_path"))

    @property
    def visible_columns(self) -> list[str]:
        return [column for column, visible in self.column_dict.items() if visible]

    @property
    def columns(self) -> list[str]:
        return [column for column in self.config["column.visibility"].keys()]

    def set_tasks_always_expanded(self, new_value: bool):
        self.tasks_always_expanded = new_value
        self.config.set(
            section="kanban.settings",
            option="tasks_always_expanded",
            value=f"{new_value}",
        )
        self.save()

    def set_no_category_task_color(self, new_value: str) -> None:
        self.no_category_task_color = new_value
        self.config.set(
            section="kanban.settings", option="no_category_task_color", value=new_value
        )
        self.save()

    def set_column_dict(self, column_name: str):
        self.column_dict.update({column_name: not self.column_dict[column_name]})
        self.config.set(
            section="column.visibility",
            option=column_name,
            value="False"
            if self.config.getboolean(section="column.visibility", option=column_name)
            == "False"
            else "True",
        )
        self.save()

    def add_category(self, category: str, color: str):
        self.category_color_dict[category] = color
        self.save()

    # @property
    # def start_column(self) -> bool:
    #     return self.config.getint(section="kanban.settings", option="start_column")

    # @start_column.setter
    # def start_column(self, new_value: int):
    #     self.config.set(
    #         section="kanban.settings",
    #         option="start_column",
    #         value=f"{new_value}",
    #     )
    #     self.save()

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
    config["column.visibility"] = {
        "Ready": True,
        "Doing": True,
        "Done": True,
        "Archive": False,
    }
    config["kanban.settings"] = {
        "tasks_always_expanded": False,
        "no_category_task_color": "#004578",  # $primary
        # "start_column": 0,
    }

    with open(config_path, "w") as conf_file:
        config.write(conf_file)
