from __future__ import annotations
import os
from contextvars import ContextVar
from typing import Type
from pathlib import Path
from enum import StrEnum

import tomli_w
from pydantic import BaseModel, Field
from pydantic_settings import (
    BaseSettings,
    TomlConfigSettingsSource,
    PydanticBaseSettingsSource,
)

from kanban_tui.constants import (
    AUTH_FILE,
    CONFIG_FILE,
    DATABASE_FILE,
)


class Backends(StrEnum):
    SQLITE = "sqlite"
    JIRA = "jira"
    CUSTOM = "custom"


class MovementModes(StrEnum):
    ADJACENT = "adjacent"
    JUMP = "jump"


class BoardSettings(BaseModel):
    theme: str = Field(default="dracula")
    columns_in_view: int = Field(default=3)


class TaskSettings(BaseModel):
    default_color: str = Field(default="#004578")
    always_expanded: bool = Field(default=False)
    movement_mode: MovementModes = Field(default=MovementModes.ADJACENT)


class JqlEntry(BaseModel):
    id: int
    name: str
    jql: str


class JiraBackendSettings(BaseModel):
    base_url: str = Field(default="")
    auth_file_path: str = Field(default=AUTH_FILE.as_posix())
    jqls: list[JqlEntry] = Field(default_factory=list)
    active_jql: int = Field(default=1)


class SqliteBackendSettings(BaseModel):
    database_path: str = Field(default=DATABASE_FILE.as_posix())
    active_board_id: int = Field(default=1)


class BackendSettings(BaseModel):
    mode: Backends = Field(default=Backends.SQLITE)
    sqlite_settings: SqliteBackendSettings = Field(
        default_factory=SqliteBackendSettings
    )
    jira_settings: JiraBackendSettings = Field(default_factory=JiraBackendSettings)


class Settings(BaseSettings):
    board: BoardSettings = Field(default_factory=BoardSettings)
    task: TaskSettings = Field(default_factory=TaskSettings)
    backend: BackendSettings = Field(default_factory=BackendSettings)

    def set_columns_in_view(self, new_columns_in_view: int) -> None:
        self.board.columns_in_view = new_columns_in_view
        self.save()

    def set_theme(self, new_theme: str) -> None:
        self.board.theme = new_theme
        self.save()

    def set_task_always_expanded(self, new_value: bool) -> None:
        self.task.always_expanded = new_value
        self.save()

    def set_task_default_color(self, new_color: str) -> None:
        self.task.default_color = new_color
        self.save()

    def set_task_movement_mode(self, new_mode: MovementModes) -> None:
        self.task.movement_mode = new_mode
        self.save()

    def set_backend(self, new_backend: Backends) -> None:
        self.backend.mode = new_backend
        self.save()

    def set_db_path(self, new_db_path: str) -> None:
        self.backend.sqlite_settings.database_path = new_db_path
        self.save()

    def set_active_board(self, new_active_board_id: int) -> None:
        self.backend.sqlite_settings.active_board_id = new_active_board_id
        self.save()

    def add_jql(self, new_jql: JqlEntry) -> None:
        self.backend.jira_settings.jqls.append(new_jql)
        self.save()

    def remove_jql(self, jql_to_remove: JqlEntry) -> None:
        for jql in self.backend.jira_settings.jqls:
            if jql == jql_to_remove:
                self.backend.jira_settings.jqls.remove(jql_to_remove)
        self.save()

    def save(self, path: str = CONFIG_FILE.as_posix()):
        config_from_env = os.getenv("KANBAN_TUI_CONFIG_FILE")
        if config_from_env:
            path = config_from_env
        with open(Path(path).resolve(), "w") as toml_file:
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


def init_config(config_path: str, database: str) -> str:
    if Path(config_path).exists():
        return "Config Exists"

    config = Settings()
    config.set_db_path(database)
    config.save(config_path)
    return "Config Created"


SETTINGS: ContextVar[Settings] = ContextVar("settings")
