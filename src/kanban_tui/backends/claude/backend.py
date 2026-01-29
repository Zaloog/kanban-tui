from __future__ import annotations
import os
import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from kanban_tui.backends.base import Backend
from kanban_tui.classes.board import Board
from kanban_tui.classes.category import Category
from kanban_tui.classes.column import Column
from kanban_tui.classes.task import Task
from kanban_tui.config import ClaudeBackendSettings


@dataclass
class ClaudeBackend(Backend):
    """Read-only backend for Claude Code task lists.

    Reads tasks from ~/.claude/tasks/SESSION_ID/*.json files and presents
    them as kanban boards. Each session becomes a board, and task statuses
    map to columns:
    - pending → Ready (column 1)
    - in_progress → Doing (column 2)
    - completed → Done (column 3)

    This backend is read-only to avoid conflicts with Claude Code's task
    management system.
    """

    settings: ClaudeBackendSettings

    def __post_init__(self):
        if path := os.getenv("CLAUDE_CODE_CONFIG_DIR"):
            path = Path(path) / "tasks"
        else:
            path = Path(self.settings.tasks_base_path)

        self._tasks_base_path = path.expanduser()
        self._status_to_column_id = {
            "pending": 1,
            "in_progress": 2,
            "completed": 3,
        }
        self._column_id_to_status = {
            column_id: status for status, column_id in self._status_to_column_id.items()
        }

    # === Board Management ===

    def get_boards(self) -> list[Board]:
        """Get all boards (one per Claude session directory)."""
        if not self._tasks_base_path.exists():
            return []

        boards = []
        for idx, session_dir in enumerate(
            sorted(self._tasks_base_path.iterdir()), start=1
        ):
            if session_dir.is_dir():
                boards.append(
                    Board(
                        board_id=idx,
                        name=session_dir.name,
                        icon="🤖",
                        creation_date=datetime.fromtimestamp(
                            session_dir.stat().st_ctime
                        ),
                        reset_column=1,
                        start_column=2,
                        finish_column=3,
                    )
                )
        return boards

    @property
    def active_board(self) -> Board:
        """Get the currently active board based on settings."""
        boards = self.get_boards()
        if not boards:
            raise Exception("No Claude task sessions found")

        # If active_session_id is set, find that board
        if self.settings.active_session_id:
            for board in boards:
                if board.name == self.settings.active_session_id:
                    return board
        # Default to first board
        return boards[0]

    # === Column Management ===

    def get_columns(self, board_id: int | None = None) -> list[Column]:
        """Get columns for a board (always 3: Ready, Doing, Done)."""
        if board_id is None:
            board_id = self.active_board.board_id

        return [
            Column(
                column_id=index,
                name=name,
                visible=True,
                position=index - 1,
                board_id=board_id,
            )
            for name, index in self._status_to_column_id.items()
        ]

    # === Task Management ===

    def _read_task_file(self, task_file: Path) -> dict[str, Any] | None:
        """Read and parse a Claude task JSON file."""
        try:
            with open(task_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def _claude_task_to_kanban(
        self, claude_task: dict[str, Any], board_id: int
    ) -> Task:
        """Convert a Claude task dict to a Kanban Task object."""
        task_id = int(claude_task["id"])
        status = claude_task.get("status", "pending")
        column_id = self._status_to_column_id.get(status, 1)

        # Parse blockedBy and blocks as integers
        blocked_by = [int(x) for x in claude_task.get("blockedBy", [])]
        blocking = [int(x) for x in claude_task.get("blocks", [])]

        # Determine dates based on status
        now = datetime.now()
        creation_date = now
        start_date = now if status in ("in_progress", "completed") else None
        finish_date = now if status == "completed" else None

        return Task(
            task_id=task_id,
            title=claude_task.get("subject", "Untitled Task"),
            description=claude_task.get("description", ""),
            column=column_id,
            creation_date=creation_date,
            start_date=start_date,
            finish_date=finish_date,
            category=None,
            due_date=None,
            blocked_by=blocked_by,
            blocking=blocking,
            metadata={
                "activeForm": claude_task.get("activeForm", ""),
                "source": "claude",
                "session_id": self._get_session_id_for_board(board_id),
            },
        )

    def _get_session_id_for_board(self, board_id: int) -> str:
        """Get session ID for a board ID."""
        boards = self.get_boards()
        for board in boards:
            if board.board_id == board_id:
                return board.name
        return ""

    def _get_session_path(self, board_id: int) -> Path:
        """Get the file system path for a session/board."""
        session_id = self._get_session_id_for_board(board_id)
        return self._tasks_base_path / session_id

    def get_tasks_on_active_board(self) -> list[Task]:
        """Get all tasks on the active board."""
        return self.get_tasks_by_board(self.active_board.board_id)

    def get_tasks_by_board(self, board_id: int) -> list[Task]:
        """Get all tasks for a specific board/session."""
        session_path = self._get_session_path(board_id)
        if not session_path.exists():
            return []

        tasks = []
        for task_file in sorted(session_path.glob("*.json")):
            claude_task = self._read_task_file(task_file)
            if claude_task:
                tasks.append(self._claude_task_to_kanban(claude_task, board_id))

        return tasks

    def get_task_by_id(self, task_id: int) -> Task | None:
        """Get a specific task by ID."""
        all_tasks = self.get_tasks_on_active_board()
        for task in all_tasks:
            if task.task_id == task_id:
                return task
        return None

    def get_tasks_by_ids(self, task_ids: list[int]) -> list[Task]:
        """Fetch multiple tasks by their IDs."""
        all_tasks = self.get_tasks_on_active_board()
        return [t for t in all_tasks if t.task_id in task_ids]

    def get_column_by_id(self, column_id: int) -> Column | None:
        """Get a column by ID."""
        columns = self.get_columns()
        for column in columns:
            if column.column_id == column_id:
                return column
        return None

    # === Read-Only Stubs (Operations Not Supported) ===

    def create_new_board(
        self,
        name: str,
        icon: str | None = None,
        column_dict: dict[str, bool] | None = None,
    ) -> Board:
        raise NotImplementedError("Claude backend is read-only. Cannot create boards.")

    def delete_board(self, board_id: int):
        board_path = self._get_session_path(board_id)
        shutil.rmtree(board_path)

    def update_board(self, board_id: int, name: str, icon: str):
        raise NotImplementedError("Claude backend is read-only. Cannot update boards.")

    def create_new_task(
        self,
        title: str,
        description: str,
        column: int,
        category: int | None = None,
        due_date: datetime | None = None,
    ) -> Task:
        raise NotImplementedError("Claude backend is read-only. Cannot create tasks.")

    def get_task_file_path(self, task_id: int) -> Path:
        task_name = f"{task_id}.json"
        return self._get_session_path(self.active_board.board_id) / task_name

    def update_task_status_json(
        self, task_path: Path, target_status: int
    ) -> dict[str, Any] | None:
        json_dict = self._read_task_file(task_path)
        if json_dict:
            json_dict["status"] = self._column_id_to_status.get(target_status)
        return json_dict

    def save_json(self, target_path: Path, json_dict):
        json_string = json.dumps(json_dict)
        target_path.write_text(json_string, encoding="utf-8")

    def update_task_status(self, new_task: Task):
        task_path = self.get_task_file_path(new_task.task_id)
        new_json_dict = self.update_task_status_json(task_path, new_task.column)
        self.save_json(task_path, new_json_dict)

    def update_task_json(
        self, task_path: Path, title: str, description: str
    ) -> dict[str, Any] | None:
        json_dict = self._read_task_file(task_path)
        if json_dict:
            json_dict["subject"] = title
            json_dict["description"] = description
        return json_dict

    def update_task_entry(
        self,
        task_id: int,
        title: str,
        description: str,
        category: int | None,
        due_date: datetime | None,
    ) -> Task | None:
        task_path = self.get_task_file_path(task_id)
        new_json_dict = self.update_task_json(task_path, title, description)
        self.save_json(task_path, new_json_dict)
        if new_json_dict:
            return self._claude_task_to_kanban(
                new_json_dict, self.active_board.board_id
            )
        return None

    def create_new_category(self, name: str, color: str) -> Category:
        raise NotImplementedError(
            "Claude backend is read-only. Cannot create categories."
        )

    def delete_task(self, task_id: int):
        task_path = self.get_task_file_path(task_id)
        task_path.unlink(missing_ok=True)

    def update_category(self, category_id: int, name: str, color: str) -> Category:
        raise NotImplementedError(
            "Claude backend is read-only. Cannot update categories."
        )

    def delete_category(self, category_id: int):
        raise NotImplementedError(
            "Claude backend is read-only. Cannot delete categories."
        )

    def get_all_categories(self) -> list[Category]:
        return []  # No categories in Claude backend

    def get_category_by_id(self, category_id: int) -> Category:
        raise NotImplementedError("Claude backend does not support categories.")

    def update_column_visibility(self, column_id: int, visible: bool):
        raise NotImplementedError(
            "Claude backend is read-only. Cannot update column visibility."
        )

    def update_column_name(self, column_id: int, new_name: str):
        raise NotImplementedError(
            "Claude backend is read-only. Cannot update column names."
        )

    def get_board_infos(self):
        """Get board information for all sessions."""
        boards = self.get_boards()
        return [
            {
                "board_id": board.board_id,
                "name": board.name,
                "icon": board.icon,
                "amount_tasks": len(self.get_tasks_by_board(board.board_id)),
                "amount_columns": len(self.get_columns(board.board_id)),
                "next_due": None,  # Claude backend doesn't use due dates
            }
            for board in boards
        ]

    # === Task Dependencies (Read-Only) ===

    def create_task_dependency(self, task_id: int, depends_on_task_id: int) -> int:
        raise NotImplementedError(
            "Claude backend is read-only. Cannot create dependencies."
        )

    def delete_task_dependency(self, task_id: int, depends_on_task_id: int) -> int:
        raise NotImplementedError(
            "Claude backend is read-only. Cannot delete dependencies."
        )

    def would_create_dependency_cycle(
        self, task_id: int, depends_on_task_id: int
    ) -> bool:
        """Check if adding a dependency would create a cycle."""
        # Since Claude backend is read-only, this always returns False
        return False
