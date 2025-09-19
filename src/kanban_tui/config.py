import os
from contextvars import ContextVar
from typing import Any, Literal, Type
from pathlib import Path

import yaml
import tomli_w
from pydantic import BaseModel, __version__, Field
from pydantic_settings import (
    BaseSettings,
    TomlConfigSettingsSource,
    PydanticBaseSettingsSource,
)

from kanban_tui.constants import CONFIG_FILE, CONFIG_FULL_PATH, DB_FULL_PATH


class KanbanTuiConfig(BaseModel):
    config_path: Path = CONFIG_FULL_PATH
    database_path: Path = DB_FULL_PATH
    config: dict[str, Any] = {}
    tasks_always_expanded: bool = False
    no_category_task_color: str = "#004578"
    active_board: int = 1
    theme: str = "dracula"
    category_color_dict: dict[str | None, str] = {}
    work_hour_dict: dict[str, str] = {
        "start_hour": "00",
        "start_min": "00",
        "end_hour": "00",
        "end_min": "00",
    }

    if __version__.startswith("1"):

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.config = self.load()
            self.theme = self.config["kanban.settings"].get("theme", "dracula")
            self.tasks_always_expanded = self.config["kanban.settings"][
                "tasks_always_expanded"
            ]
            self.no_category_task_color = self.config["kanban.settings"][
                "no_category_task_color"
            ]
            self.active_board = self.config["kanban.settings"]["active_board"]
            self.category_color_dict = self.config["category.colors"]

            self.work_hour_dict = self.config["kanban.settings"]["work_hours"]
            self.database_path = Path(self.config["database"]["database_path"])

    else:

        def model_post_init(self, __context: Any) -> None:
            self.config = self.load()
            self.theme = self.config["kanban.settings"].get("theme", "dracula")
            self.tasks_always_expanded = self.config["kanban.settings"][
                "tasks_always_expanded"
            ]
            self.no_category_task_color = self.config["kanban.settings"][
                "no_category_task_color"
            ]
            self.active_board = self.config["kanban.settings"]["active_board"]
            self.category_color_dict = self.config["category.colors"]

            self.work_hour_dict = self.config["kanban.settings"]["work_hours"]
            self.database_path = Path(self.config["database"]["database_path"])

    def set_active_board(self, new_active_board: int) -> None:
        self.active_board = new_active_board
        self.config["kanban.settings"]["active_board"] = new_active_board
        self.save()

    def set_tasks_always_expanded(self, new_value: bool) -> None:
        self.tasks_always_expanded = new_value
        self.config["kanban.settings"]["tasks_always_expanded"] = new_value
        self.save()

    def set_no_category_task_color(self, new_color: str) -> None:
        self.no_category_task_color = new_color
        self.config["kanban.settings"]["no_category_task_color"] = new_color
        self.save()

    def add_category(self, category: str, color: str) -> None:
        self.category_color_dict[category] = color
        self.save()

    def set_work_hour_dict(self, entry: str, new_value: str) -> None:
        self.work_hour_dict.update({entry: new_value})
        self.config["kanban.settings"]["work_hours"].update(self.work_hour_dict)
        self.save()

    def set_theme(self, new_theme: str) -> None:
        self.theme = new_theme
        self.config["kanban.settings"]["theme"] = new_theme
        self.save()

    def load(self) -> dict[str, Any]:
        with open(self.config_path, "r") as yaml_file:
            return yaml.safe_load(yaml_file)

    def save(self) -> None:
        with open(self.config_path, "w") as yaml_file:
            dump = yaml.dump(self.config, sort_keys=False, indent=4, line_break="\n")
            yaml_file.write(dump)


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
    config["kanban.settings"] = {
        "tasks_always_expanded": False,
        "active_board": 1,
        "no_category_task_color": "#004578",
        "theme": "dracula",
        "work_hours": {
            "start_hour": "00",
            "start_min": "00",
            "end_hour": "00",
            "end_min": "00",
        },
    }

    with open(config_path, "w") as yaml_file:
        dump = yaml.dump(config, sort_keys=False, indent=4, line_break="\n")
        yaml_file.write(dump)

    return "Config Created"


class BoardSettings(BaseModel):
    theme: str = Field(default="dracula")
    columns_in_view: int = Field(default=3)


class TaskSettings(BaseModel):
    default_color: str = Field(default="#004578")
    always_expanded: bool = Field(default=False)


class JiraBackendSettings(BaseModel):
    user: str = Field(default="")
    api_token: str = Field(default="")
    url: str = Field(default="")


class SqliteBackendSettings(BaseModel):
    database_path: str = Field(default=DB_FULL_PATH.as_posix())
    active_board_id: int = Field(default=1)


class BackendSettings(BaseModel):
    mode: Literal["sqlite", "jira"] = Field(default="sqlite")
    sqlite_settings: SqliteBackendSettings = Field(
        default_factory=SqliteBackendSettings
    )
    jira_settings: JiraBackendSettings = Field(default_factory=JiraBackendSettings)


class Settings(BaseSettings):
    # database_path: Path = DB_FULL_PATH
    board: BoardSettings = Field(default_factory=BoardSettings)
    task: TaskSettings = Field(default_factory=TaskSettings)
    backend: BackendSettings = Field(default_factory=BackendSettings)

    def set_columns_in_view(self, new_columns_in_view: int):
        self.board.columns_in_view = new_columns_in_view
        self.save()

    def set_theme(self, new_theme: str):
        self.board.theme = new_theme
        self.save()

    def set_tasks_always_expanded(self, new_value: bool) -> None:
        self.task.always_expanded = new_value
        self.save()

    def set_default_task_color(self, new_color: str) -> None:
        self.task.default_color = new_color
        self.save()

    def set_backend(self, new_backend: Literal["sqlite", "jira"]) -> None:
        self.backend.mode = new_backend
        self.save()

    def set_db_path(self, new_db_path: str):
        self.backend.sqlite_settings.database_path = new_db_path
        self.save()

    def set_active_board(self, new_active_board_id: int) -> None:
        self.backend.sqlite_settings.active_board_id = new_active_board_id
        self.save()

    # TODO
    # def add_category(self, category: str, color: str) -> None:
    #     self.category_color_dict[category] = color
    #     self.save()

    def save(self, path: Path = CONFIG_FILE):
        config_from_env = os.getenv("KANBAN_TUI_CONFIG_FILE")
        if config_from_env:
            path = Path(config_from_env).resolve()
        with open(path, "w") as toml_file:
            dumb = tomli_w.dumps(self.model_dump())
            toml_file.write(dumb)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        config_from_env = os.getenv("KANBAN_TUI_CONFIG_FILE")
        if config_from_env:
            conf_file = Path(config_from_env).resolve()
        else:
            conf_file = CONFIG_FILE

        default_sources = (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )

        if conf_file.exists():
            return (
                init_settings,
                TomlConfigSettingsSource(settings_cls, conf_file),
                env_settings,
                dotenv_settings,
                file_secret_settings,
            )
        return default_sources


def init_config(config_path: Path = CONFIG_FILE, database: Path = DB_FULL_PATH) -> str:
    if config_path.exists():
        return "Config Exists"

    config = Settings()
    config.set_db_path(database.as_posix())
    config.save(config_path)


SETTINGS: ContextVar[Settings] = ContextVar("settings")
