from typing import Any
import yaml
from pathlib import Path

from pydantic import BaseModel

from kanban_tui.constants import CONFIG_FULL_PATH, DB_FULL_PATH


class KanbanTuiConfig(BaseModel):
    config_path: Path = CONFIG_FULL_PATH
    database_path: Path = DB_FULL_PATH
    config: dict[str, Any] = {}
    tasks_always_expanded: bool = False
    no_category_task_color: str = "#004578"
    category_color_dict: dict[str | None, str] = {}
    column_dict: dict[str, bool] = {
        "Ready": True,
        "Doing": True,
        "Done": True,
        "Archive": False,
    }
    work_hour_dict: dict[str, str] = {
        "start_hour": "00",
        "start_min": "00",
        "end_hour": "00",
        "end_min": "00",
    }

    def model_post_init(self, __context: Any) -> None:
        self.config = self.load()
        self.tasks_always_expanded = self.config["kanban.settings"][
            "tasks_always_expanded"
        ]
        self.no_category_task_color = self.config["kanban.settings"][
            "no_category_task_color"
        ]
        self.category_color_dict = self.config["category.colors"]
        self.column_dict = self.config["column.visibility"]
        self.work_hour_dict = self.config["kanban.settings"]["work_hours"]
        self.database_path = Path(self.config["database"]["database_path"])

    @property
    def visible_columns(self) -> list[str]:
        return [column for column, visible in self.column_dict.items() if visible]

    @property
    def columns(self) -> list[str]:
        return [column for column in self.config["column.visibility"].keys()]

    def set_tasks_always_expanded(self, new_value: bool) -> None:
        self.tasks_always_expanded = new_value
        self.config["kanban.settings"]["tasks_always_expanded"] = new_value
        self.save()

    def set_no_category_task_color(self, new_color: str) -> None:
        self.no_category_task_color = new_color
        self.config["kanban.settings"]["no_category_task_color"] = new_color
        self.save()

    def add_new_column(self, new_column: str, position: int) -> None:
        actual_columns = list(self.config["column.visibility"].items())
        actual_columns.insert(position, (new_column, True))

        self.config["column.visibility"] = dict(actual_columns)
        self.column_dict = self.config["column.visibility"]
        self.save()

    def delete_column(self, column_to_delete: str) -> None:
        self.column_dict.pop(column_to_delete)
        self.config["column.visibility"] = self.column_dict
        self.save()

    def set_column_dict(self, column_name: str) -> None:
        self.column_dict.update({column_name: not self.column_dict[column_name]})
        self.config["column.visibility"][column_name] = self.column_dict[column_name]
        self.save()

    def add_category(self, category: str, color: str) -> None:
        self.category_color_dict[category] = color
        self.save()

    def set_work_hour_dict(self, entry: str, new_value: str) -> None:
        self.work_hour_dict.update({entry: new_value})
        self.config["kanban.settings"]["work_hours"].update(self.work_hour_dict)
        self.save()

    def load(self) -> dict[str, Any]:
        with open(self.config_path, "r") as yaml_file:
            return yaml.safe_load(yaml_file)

    def save(self) -> None:
        with open(self.config_path, "w") as yaml_file:
            yaml_file.write(yaml.dump(self.config, sort_keys=False))


def init_new_config(
    config_path: Path = CONFIG_FULL_PATH, database: Path = DB_FULL_PATH
) -> str:
    if config_path.exists():
        return "Config Exists"

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.touch()

    config: dict[str, dict[str, Any]] = {}
    config["database"] = {"database_path": database.as_posix()}
    config["category.colors"] = {}
    config["column.visibility"] = {
        "Ready": True,
        "Doing": True,
        "Done": True,
        "Archive": False,
    }
    config["kanban.settings"] = {
        "tasks_always_expanded": False,
        "no_category_task_color": "#004578",
        "work_hours": {
            "start_hour": "00",
            "start_min": "00",
            "end_hour": "00",
            "end_min": "00",
        },
    }

    with open(config_path, "w") as yaml_file:
        yaml_file.write(yaml.dump(config, sort_keys=False, default_flow_style=True))

    return "Config Created"
