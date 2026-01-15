import os
from pathlib import Path
from importlib.metadata import version
from importlib.resources import files

from kanban_tui.constants import (
    CLAUDE_SKILL_NAME,
    CLAUDE_SKILL_LOCAL_DIR,
    CLAUDE_SKILL_GLOBAL_DIR,
)


def get_version() -> str:
    return f"v{version('kanban-tui')}"


def get_skill_local_path() -> Path:
    folder_path = os.getenv("KANBAN_TUI_LOCAL_SKILL", CLAUDE_SKILL_LOCAL_DIR.as_posix())
    file_path = Path(folder_path) / CLAUDE_SKILL_NAME
    return file_path


def get_skill_global_path() -> Path:
    folder_path = os.getenv(
        "CLAUDE_CODE_CONFIG_DIR", CLAUDE_SKILL_GLOBAL_DIR.as_posix()
    )
    file_path = Path(folder_path) / CLAUDE_SKILL_NAME
    return file_path


def get_skill_md_version(file_path: Path) -> str:
    skill_content = file_path.read_text(encoding="utf-8")
    version_line = skill_content.splitlines()[-1]
    version = version_line.split(" ")[2]
    return version


def get_skill_md() -> str:
    skill_content = (
        files("kanban_tui.assets").joinpath("SKILL.md").read_text(encoding="utf-8")
    )
    skill_content = skill_content.replace("KANBAN_TUI_VERSION", get_version())
    return skill_content
