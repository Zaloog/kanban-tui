import os
from pathlib import Path
from typing import Type

from pydantic import BaseModel, Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    TomlConfigSettingsSource,
)
import tomli_w

from kanban_tui.constants import AUTH_FILE


class ApiKeyEntry(BaseModel):
    api_key: str = ""
    cert_path: str = ""


class AuthSettings(BaseSettings):
    jira: ApiKeyEntry = Field(default_factory=ApiKeyEntry)

    def set_jira_api_key(self, new_api_key: str) -> None:
        self.jira.api_key = new_api_key
        self.save()

    def set_jira_cert_path(self, new_cert_path: str) -> None:
        self.jira.cert_path = new_cert_path
        self.save()

    def set_cert_path(self, new_cert_path: str) -> None:
        self.jira.cert_path = new_cert_path
        self.save()

    def save(self, path: str = AUTH_FILE.as_posix()):
        config_from_env = os.getenv("KANBAN_TUI_AUTH_FILE")
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
        config_from_env = os.getenv("KANBAN_TUI_AUTH_FILE")
        if config_from_env:
            conf_file = Path(config_from_env).resolve()
        else:
            conf_file = AUTH_FILE

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


def init_auth_file(auth_file_path: str) -> str:
    if Path(auth_file_path).exists():
        return "Auth file exists"

    config = AuthSettings()
    config.save(auth_file_path)
    return "Auth file created"
