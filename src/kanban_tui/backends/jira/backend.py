from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from kanban_tui.backends.auth import AuthSettings
from kanban_tui.backends.base import Backend
from kanban_tui.classes.board import Board
from kanban_tui.classes.category import Category
from kanban_tui.classes.column import Column
from kanban_tui.classes.task import Task
from kanban_tui.config import JiraBackendSettings, JqlEntry
from kanban_tui.backends.auth import init_auth_file
from kanban_tui.backends.jira.jira_api import (
    get_jql,
    get_jql_async,
    authenticate_to_jira,
    get_transitions,
    set_issue_status,
)
from kanban_tui.backends.jira.models import JiraIssue


@dataclass
class JiraBackend(Backend):
    settings: JiraBackendSettings
    auth: Any = field(init=False)
    auth_settings: AuthSettings = field(init=False)
    _status_column_map: dict[str, int] = field(init=False, default_factory=dict)

    def __post_init__(self):
        init_auth_file(self.settings.auth_file_path)
        self.auth_settings = AuthSettings()
        self.auth = authenticate_to_jira(
            self.settings.base_url, self.api_key, self.cert_path
        )
        self._status_column_map = self.settings.status_to_column_map

    # Queries
    def get_boards(self) -> list[Board]:
        """Return a virtual board representing the active JQL query results"""
        if not self.settings.jqls:
            return []

        active_jql_entry = self._get_active_jql_entry()
        if not active_jql_entry:
            return []

        # Create a virtual board from the JQL query
        return [
            Board(
                board_id=entry.id,
                name=entry.name,
                icon=":mag:",
                creation_date=datetime.now(),
                reset_column=1,  # To Do
                start_column=2,  # In Progress
                finish_column=3,  # Done
            )
            for entry in self.settings.jqls
        ]

    def get_all_categories(self) -> list[Category]:
        """Jira backend doesn't support categories (could map from labels later)"""
        return []

    def get_board_infos(self) -> list[dict]:
        """Return info about the virtual Jira boards"""
        boards = self.get_boards()
        if not boards:
            return []

        board_infos = []

        for board in boards:
            board_tasks = self.get_tasks_by_board_id(board_id=board.board_id)

            board_info_dict = {
                "board_id": board.board_id,
                "amount_tasks": len(board_tasks),
                "amount_columns": len(self.get_columns(board_id=board.board_id)),
                "next_due": min(
                    (t.due_date for t in board_tasks if t.due_date), default=None
                ),
            }
            board_infos.append(board_info_dict)

        return board_infos

    def get_columns(self, board_id: int | None = None) -> list[Column]:
        """Return columns based on status mapping"""
        # Create columns from unique status-to-column mappings
        if not board_id and self.active_board:
            board_id = self.active_board.board_id

        # Get the column mapping for this specific board
        status_column_map = self._get_column_mapping_for_board(board_id)

        column_names: dict[int, list] = {
            column_id: [] for column_id in set(status_column_map.values())
        }

        # Group statuses by column
        for status, column_id in status_column_map.items():
            column_names[column_id].append(status)

        # Create column objects
        columns = []
        for column_id in sorted(column_names.keys()):
            # Use the first status name as the column name
            statuses = column_names[column_id]
            name = statuses[0] if statuses else f"Column {column_id}"

            columns.append(
                Column(
                    column_id=column_id,
                    name=name,
                    visible=True,
                    position=column_id - 1,
                    board_id=board_id,
                )
            )

        return columns

    def get_column_by_id(self, column_id: int) -> Column | None:
        """Return a single column by its ID"""
        for column in self.get_columns():
            if column.column_id == column_id:
                return column
        return None

    def get_tasks_by_board_id(self, board_id: int) -> list[Task]:
        """Execute active JQL query and convert issues to Tasks"""

        board_jql_entry = [
            entry for entry in self.settings.jqls if entry.id == board_id
        ][0]

        # Execute JQL query
        jql_result = get_jql(self.auth, board_jql_entry.jql)
        issues = jql_result.get("issues", [])

        # Convert issues to tasks
        tasks = []
        for issue_data in issues:
            try:
                task = self._jira_issue_to_task(issue_data, board_id=board_id)
                tasks.append(task)
            except Exception as e:
                raise e

        # Resolve dependencies
        self._resolve_issue_dependencies(tasks, issues)
        return tasks

    async def get_tasks_by_board_id_async(self, board_id: int) -> list[Task]:
        """Execute active JQL query and convert issues to Tasks (async, non-blocking)"""

        board_jql_entry = [
            entry for entry in self.settings.jqls if entry.id == board_id
        ][0]

        # Execute JQL query asynchronously in thread pool
        jql_result = await get_jql_async(self.auth, board_jql_entry.jql)
        issues = jql_result.get("issues", [])

        # Convert issues to tasks
        tasks = []
        for issue_data in issues:
            try:
                task = self._jira_issue_to_task(issue_data, board_id=board_id)
                tasks.append(task)
            except Exception as e:
                raise e

        # Resolve dependencies
        self._resolve_issue_dependencies(tasks, issues)
        return tasks

    def get_tasks_on_active_board(self) -> list[Task]:
        """Execute active JQL query and convert issues to Tasks"""
        return self.get_tasks_by_board_id(board_id=self.settings.active_jql)

    async def get_tasks_on_active_board_async(self) -> list[Task]:
        """Execute active JQL query and convert issues to Tasks (async, non-blocking)"""
        return await self.get_tasks_by_board_id_async(board_id=self.settings.active_jql)

    def get_task_by_id(self, task_id: int) -> Task | None:
        """Fetch a single Jira issue by ID"""
        tasks = self.get_tasks_by_ids([task_id])
        return tasks[0] if tasks else None

    def get_tasks_by_ids(self, task_ids: list[int]) -> list[Task]:
        """Fetch specific Jira issues by ID"""
        if not task_ids:
            return []

        # Fetch from Jira API
        tasks = []
        for task_id in task_ids:
            try:
                jql = f'id = "{task_id}"'
                result = get_jql(self.auth, jql)
                issues = result.get("issues", [])
                if issues:
                    task = self._jira_issue_to_task(issues[0])
                    tasks.append(task)
            except Exception as e:
                print(f"Error fetching task {task_id}: {e}")
                continue

        return tasks

    # Helper methods

    def _get_active_jql_entry(self):
        """Get the active JQL entry"""
        if not self.settings.jqls:
            return None

        for entry in self.settings.jqls:
            if entry.id == self.settings.active_jql:
                return entry

        # Fallback to first entry
        return self.settings.jqls[0] if self.settings.jqls else None

    def _jira_issue_to_task(
        self, issue_data: dict, board_id: int | None = None
    ) -> Task:
        """Convert Jira issue dict to Task model"""
        jira_issue = JiraIssue(**issue_data)

        # Map Jira status to column using board-specific mapping
        column_id = self._status_to_column(jira_issue.status, board_id)

        # Compute start/finish dates based on status category
        start_date = None
        finish_date = None

        status_category = jira_issue.status_category.lower()
        if status_category == "in progress":
            start_date = jira_issue.created
        elif status_category == "done":
            start_date = jira_issue.created
            finish_date = (
                jira_issue.resolution_date or jira_issue.updated or datetime.now()
            )

        # Use Jira's numeric ID as task_id (must be int)
        # Store the Jira key in metadata
        task_id = int(jira_issue.id)

        # Build metadata with Jira-specific fields
        metadata = {
            "jira_key": jira_issue.key,
            "assignee": jira_issue.assignee,
            "assignee_email": jira_issue.assignee_email,
            "reporter": jira_issue.reporter,
            "priority": jira_issue.priority,
            "issue_type": jira_issue.issue_type,
            "labels": jira_issue.labels,
            "components": jira_issue.components,
            "status": jira_issue.status,
            "status_category": jira_issue.status_category,
            "updated": jira_issue.updated.isoformat() if jira_issue.updated else None,
            "resolution": jira_issue.resolution,
            "backend_source": "jira",
        }

        return Task(
            task_id=task_id,
            title=f"{jira_issue.key}\n{jira_issue.summary}",
            column=column_id,
            creation_date=jira_issue.created,
            start_date=start_date,
            finish_date=finish_date,
            due_date=jira_issue.due_date,
            description=jira_issue.description,
            category=None,  # Could map from labels/components later
            blocked_by=[],  # Will be populated by _resolve_issue_dependencies
            blocking=[],
            metadata=metadata,
        )

    def _get_column_mapping_for_board(self, board_id: int | None) -> dict[str, int]:
        """Get the column mapping for a specific board"""
        if board_id is None:
            return self._status_column_map

        # Find the JQL entry for this board
        jql_entry = next(
            (entry for entry in self.settings.jqls if entry.id == board_id), None
        )

        if jql_entry and jql_entry.column_mapping:
            return jql_entry.column_mapping

        # Fallback to global mapping
        return self._status_column_map

    def _status_to_column(self, status: str, board_id: int | None = None) -> int:
        """Map Jira status to kanban column"""
        column_mapping = self._get_column_mapping_for_board(board_id)
        return column_mapping.get(status, 1)  # Default to first column

    def _resolve_issue_dependencies(self, tasks: list[Task], issues: list[dict]):
        """Resolve Jira issue links to task dependencies"""
        # Build lookup for issue keys/IDs to tasks
        key_to_task = {}
        id_to_task = {}

        for issue, task in zip(issues, tasks):
            key_to_task[issue["key"]] = task
            id_to_task[issue["id"]] = task

        # Process issue links
        for issue, task in zip(issues, tasks):
            issue_links = issue.get("fields", {}).get("issuelinks", [])

            for link in issue_links:
                link_type = link.get("type", {})
                link_type_name = link_type.get("name", "").lower()

                # Handle outward links (current issue blocks/depends on other)
                if "outwardIssue" in link:
                    outward_issue = link["outwardIssue"]
                    # outward_key = outward_issue.get("key")
                    outward_id = outward_issue.get("id")

                    # Check if it's a "blocks" or "depends on" relationship
                    if "block" in link_type_name:
                        # Current issue blocks the outward issue
                        if outward_id and outward_id in id_to_task:
                            outward_task = id_to_task[outward_id]
                            if int(outward_task.task_id) not in task.blocking:
                                task.blocking.append(int(outward_task.task_id))
                    elif "depend" in link_type_name:
                        # Current issue depends on the outward issue
                        if outward_id and outward_id in id_to_task:
                            outward_task = id_to_task[outward_id]
                            if int(outward_task.task_id) not in task.blocked_by:
                                task.blocked_by.append(int(outward_task.task_id))

                # Handle inward links (other issue blocks/depends on current)
                if "inwardIssue" in link:
                    inward_issue = link["inwardIssue"]
                    # inward_key = inward_issue.get("key")
                    inward_id = inward_issue.get("id")

                    # Check if it's a "blocks" or "depends on" relationship
                    if "block" in link_type_name:
                        # Inward issue blocks current issue
                        if inward_id and inward_id in id_to_task:
                            inward_task = id_to_task[inward_id]
                            if int(inward_task.task_id) not in task.blocked_by:
                                task.blocked_by.append(int(inward_task.task_id))
                    elif "depend" in link_type_name:
                        # Inward issue depends on current issue
                        if inward_id and inward_id in id_to_task:
                            inward_task = id_to_task[inward_id]
                            if int(inward_task.task_id) not in task.blocking:
                                task.blocking.append(int(inward_task.task_id))

    @property
    def active_board(self) -> Board | None:
        boards = self.get_boards()
        if self.settings.active_jql:
            for board in boards:
                if board.board_id == self.settings.active_jql:
                    return board
        # Default to first board
        return boards[0]

    @property
    def api_key(self) -> str:
        return self.auth_settings.jira.api_key

    @property
    def cert_path(self) -> str:
        return self.auth_settings.jira.cert_path

    # Read-only backend - these methods raise NotImplementedError

    def create_new_task(self, *args, **kwargs):
        raise NotImplementedError(
            "Jira backend is read-only. Create tasks in Jira directly."
        )

    def update_task_entry(self, *args, **kwargs):
        raise NotImplementedError(
            "Jira backend is read-only. Update tasks in Jira directly."
        )

    def delete_task(self, *args, **kwargs):
        raise NotImplementedError(
            "Jira backend is read-only. Delete tasks in Jira directly."
        )

    def update_task_status(self, new_task: Task) -> dict[str, bool | str]:
        """Update Jira issue status by finding a transition whose target
        status maps to the same column the task was moved to.

        Args:
            new_task: Task with updated column information

        Returns:
            dict with 'success' (bool) and 'message' (str) keys
        """
        jira_key = new_task.metadata.get("jira_key")
        if not jira_key:
            return {
                "success": False,
                "message": "Task does not have a Jira key in metadata",
            }

        board_id = self.active_board.board_id if self.active_board else None
        target_column = new_task.column

        try:
            transitions = get_transitions(self.auth, jira_key)
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to fetch transitions: {str(e)}",
            }

        # For each transition, map its target status back to a column ID
        # using the column mapping lookup, then compare column IDs
        # (int == int) instead of comparing status name strings.
        column_mapping = self._get_column_mapping_for_board(board_id)
        transition_id = None
        available = []

        for transition in transitions:
            if not isinstance(transition, dict):
                continue

            to_status = transition.get("to", "")
            column_for_transition = column_mapping.get(to_status)
            available.append(f"{to_status} (col {column_for_transition})")

            if (
                column_for_transition is not None
                and column_for_transition == target_column
            ):
                transition_id = transition.get("id")
                break

        if transition_id is None:
            return {
                "success": False,
                "message": f"No transition available to column {target_column}. Available: {', '.join(available)}",
            }

        return set_issue_status(self.auth, jira_key, transition_id)

    def create_new_board(
        self, name: str, jql: str, column_mapping: dict[str, int] | None = None
    ) -> int:
        if self.settings.jqls:
            new_id = self.settings.jqls[-1].id + 1
        else:
            new_id = 1

        new_jql = JqlEntry(
            id=new_id, name=name, jql=jql, column_mapping=column_mapping or {}
        )
        self.settings.jqls.append(new_jql)
        return new_id

    def update_board_entry(self, *args, **kwargs):
        raise NotImplementedError("Jira backend is read-only. Update boards in config.")

    def delete_board(self, board_id: int):
        for jql in self.settings.jqls:
            if board_id == jql.id:
                jql_to_delete = jql

        self.settings.jqls.remove(jql_to_delete)

    def create_new_column(self, *args, **kwargs):
        raise NotImplementedError(
            "Jira backend is read-only. Columns are mapped from Jira statuses."
        )

    def update_column_visibility(self, *args, **kwargs):
        raise NotImplementedError(
            "Jira backend is read-only. Update column visibility in config."
        )

    def switch_column_positions(self, *args, **kwargs):
        raise NotImplementedError(
            "Jira backend is read-only. Column positions are fixed."
        )

    def update_column_name(self, *args, **kwargs):
        raise NotImplementedError(
            "Jira backend is read-only. Column names come from Jira statuses."
        )

    def delete_column(self, *args, **kwargs):
        raise NotImplementedError(
            "Jira backend is read-only. Columns cannot be deleted."
        )

    def create_new_category(self, *args, **kwargs):
        raise NotImplementedError("Jira backend doesn't support categories.")

    def update_category_entry(self, *args, **kwargs):
        raise NotImplementedError("Jira backend doesn't support categories.")

    def delete_category(self, *args, **kwargs):
        raise NotImplementedError("Jira backend doesn't support categories.")

    def create_task_dependency(self, *args, **kwargs):
        raise NotImplementedError(
            "Jira backend is read-only. Create dependencies in Jira directly."
        )

    def delete_task_dependency(self, *args, **kwargs):
        raise NotImplementedError(
            "Jira backend is read-only. Delete dependencies in Jira directly."
        )
