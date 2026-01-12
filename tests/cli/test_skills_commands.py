import os
from pathlib import Path

from click.testing import CliRunner

from kanban_tui.cli import cli
from kanban_tui.skills import get_skill_md, get_skill_local_path, get_skill_global_path


def test_skill_local_creation(tmp_path: Path):
    os.environ["KANBAN_TUI_LOCAL_SKILL"] = tmp_path.as_posix()
    file_path = get_skill_local_path()
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["skill", "init"], input="n")
        assert result.exit_code == 0
        assert file_path.exists()
        output = result.output.replace("\n", "")
        assert (
            output
            == f"Create SKILL.md in global skills folder under {get_skill_global_path()}? [y/N]: nSKILL.md file created under {file_path}."
        )
        assert file_path.read_text(encoding="utf-8") == get_skill_md()


def test_skill_local_creation_already_exists(tmp_path: Path):
    os.environ["KANBAN_TUI_LOCAL_SKILL"] = tmp_path.as_posix()
    file_path = get_skill_local_path()
    file_path.touch()
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["skill", "init"], input="n")
        assert result.exit_code == 0
        output = result.output.replace("\n", "")
        assert (
            output
            == f"Create SKILL.md in global skills folder under {get_skill_global_path()}? [y/N]: nSKILL.md file under {file_path} already exists."
        )


def test_skill_global_creation(tmp_path: Path):
    os.environ["CLAUDE_CODE_CONFIG_DIR"] = tmp_path.as_posix()
    file_path = get_skill_global_path()
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["skill", "init"], input="y")
        assert result.exit_code == 0
        assert file_path.exists()
        output = result.output.replace("\n", "")
        assert (
            output
            == f"Create SKILL.md in global skills folder under {file_path}? [y/N]: ySKILL.md file created under {file_path}."
        )
        assert file_path.read_text(encoding="utf-8") == get_skill_md()


def test_skill_global_creation_already_exists(tmp_path: Path):
    os.environ["CLAUDE_CODE_CONFIG_DIR"] = tmp_path.as_posix()
    file_path = get_skill_global_path()
    file_path.touch()
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["skill", "init"], input="y")
        assert result.exit_code == 0
        output = result.output.replace("\n", "")
        assert (
            output
            == f"Create SKILL.md in global skills folder under {file_path}? [y/N]: ySKILL.md file under {file_path} already exists."
        )
