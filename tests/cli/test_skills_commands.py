import os
from pathlib import Path

from click.testing import CliRunner

from kanban_tui.cli import cli
from kanban_tui.constants import CLAUDE_SKILL_NAME, CLAUDE_SKILL_GLOBAL_FILE


def test_skills_local_creation(tmp_path: Path):
    os.environ["KANBAN_TUI_LOCAL_SKILL"] = tmp_path.as_posix()
    file_path = tmp_path / CLAUDE_SKILL_NAME
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["skills"], input="n")
        assert result.exit_code == 0
        assert file_path.exists()
        output = result.output.replace("\n", "")
        assert (
            output
            == f"Create SKILL.md in global skills folder under {CLAUDE_SKILL_GLOBAL_FILE}? [y/N]: nSKILL.md file created under {file_path}."
        )


def test_skills_local_creation_already_exists(tmp_path: Path):
    os.environ["KANBAN_TUI_LOCAL_SKILL"] = tmp_path.as_posix()
    file_path = tmp_path / CLAUDE_SKILL_NAME
    file_path.touch()
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["skills"], input="n")
        assert result.exit_code == 0
        output = result.output.replace("\n", "")
        assert (
            output
            == f"Create SKILL.md in global skills folder under {CLAUDE_SKILL_GLOBAL_FILE}? [y/N]: nSKILL.md file under {file_path} already exists."
        )


def test_skills_global_creation(tmp_path: Path):
    os.environ["CLAUDE_CODE_CONFIG_DIR"] = tmp_path.as_posix()
    file_path = tmp_path / CLAUDE_SKILL_NAME
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["skills"], input="y")
        assert result.exit_code == 0
        assert file_path.exists()
        output = result.output.replace("\n", "")
        assert (
            output
            == f"Create SKILL.md in global skills folder under {file_path}? [y/N]: ySKILL.md file created under {file_path}."
        )


def test_skills_global_creation_already_exists(tmp_path: Path):
    os.environ["CLAUDE_CODE_CONFIG_DIR"] = tmp_path.as_posix()
    file_path = tmp_path / CLAUDE_SKILL_NAME
    file_path.touch()
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["skills"], input="y")
        assert result.exit_code == 0
        output = result.output.replace("\n", "")
        assert (
            output
            == f"Create SKILL.md in global skills folder under {file_path}? [y/N]: ySKILL.md file under {file_path} already exists."
        )
