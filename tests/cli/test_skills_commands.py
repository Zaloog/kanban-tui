import os
from pathlib import Path

from click.testing import CliRunner

from kanban_tui.cli import cli
from kanban_tui.skills import get_skill_md, get_skill_local_path, get_skill_global_path

DELETE_OUTPUT = """Delete all kanban-tui SKILL.md files and the kanban-tui folder? [y/N]: y
Local Skill under LOCAL_SKILL_PATH deleted successfully.
Global Skill under GLOBAL_SKILL_PATH deleted successfully.
"""

CREATE_LOCAL_OUTPUT = """Create SKILL.md in global skills folder under GLOBAL_SKILL_PATH? [y/N]: n
SKILL.md file created under LOCAL_SKILL_PATH.
"""
CREATE_LOCAL_EXISTS_OUTPUT = """Create SKILL.md in global skills folder under GLOBAL_SKILL_PATH? [y/N]: n
SKILL.md file under LOCAL_SKILL_PATH already exists.
"""
CREATE_GLOBAL_OUTPUT = """Create SKILL.md in global skills folder under GLOBAL_SKILL_PATH? [y/N]: y
SKILL.md file created under GLOBAL_SKILL_PATH.
"""


def test_skill_local_creation(tmp_path: Path):
    os.environ["KANBAN_TUI_LOCAL_SKILL"] = tmp_path.as_posix()
    file_path = get_skill_local_path()
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["skill", "init"], input="n")
        assert result.exit_code == 0
        assert file_path.exists()
        output = result.output.replace(str(file_path), "LOCAL_SKILL_PATH").replace(
            str(get_skill_global_path()), "GLOBAL_SKILL_PATH"
        )
        assert output == CREATE_LOCAL_OUTPUT
        assert file_path.read_text(encoding="utf-8") == get_skill_md()


def test_skill_local_creation_already_exists(tmp_path: Path):
    os.environ["KANBAN_TUI_LOCAL_SKILL"] = tmp_path.as_posix()
    file_path = get_skill_local_path()
    file_path.touch()
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["skill", "init"], input="n")
        assert result.exit_code == 0
        output = result.output.replace(str(file_path), "LOCAL_SKILL_PATH").replace(
            str(get_skill_global_path()), "GLOBAL_SKILL_PATH"
        )
        assert output == CREATE_LOCAL_EXISTS_OUTPUT


def test_skill_global_creation(tmp_path: Path):
    os.environ["CLAUDE_CODE_CONFIG_DIR"] = tmp_path.as_posix()
    file_path = get_skill_global_path()
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["skill", "init"], input="y")
        assert result.exit_code == 0
        assert file_path.exists()
        output = result.output.replace(str(file_path), "GLOBAL_SKILL_PATH")
        assert output == CREATE_GLOBAL_OUTPUT
        assert file_path.read_text(encoding="utf-8") == get_skill_md()


def test_skill_global_creation_already_exists(tmp_path: Path):
    os.environ["CLAUDE_CODE_CONFIG_DIR"] = tmp_path.as_posix()
    file_path = get_skill_global_path()
    file_path.touch()
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["skill", "init"], input="y")
        assert result.exit_code == 0
        output = result.output.replace("\n", "").replace(
            str(file_path), "GLOBAL_SKILL_PATH"
        )
        assert output == (
            "Create SKILL.md in global skills folder under GLOBAL_SKILL_PATH? [y/N]: y"
            "SKILL.md file under GLOBAL_SKILL_PATH already exists."
        )


def test_skill_delete_no_present(tmp_path: Path):
    os.environ["CLAUDE_CODE_CONFIG_DIR"] = tmp_path.as_posix()
    os.environ["KANBAN_TUI_LOCAL_SKILL"] = tmp_path.as_posix()
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["skill", "delete"], input="n")
        assert result.exit_code == 0
        assert (
            result.output
            == "No SKILL.md files found in global and local skills folder.\n"
        )


def test_skill_delete_both(tmp_path: Path):
    os.environ["KANBAN_TUI_LOCAL_SKILL"] = (tmp_path / "local").as_posix()
    local_file_path = get_skill_local_path()
    local_file_path.parent.mkdir()
    local_file_path.touch()

    os.environ["CLAUDE_CODE_CONFIG_DIR"] = (tmp_path / "global").as_posix()
    global_file_path = get_skill_global_path()
    global_file_path.parent.mkdir()
    global_file_path.touch()
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["skill", "delete"], input="y")
        assert result.exit_code == 0
        output = result.output.replace(
            str(local_file_path), "LOCAL_SKILL_PATH"
        ).replace(str(global_file_path), "GLOBAL_SKILL_PATH")
        assert output == DELETE_OUTPUT

        assert not local_file_path.exists()
        assert not global_file_path.exists()
