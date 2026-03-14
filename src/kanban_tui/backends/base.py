class Backend:
    """Base Backend Class"""

    def get_boards(self):
        raise NotImplementedError("This is required")

    def get_columns(self):
        raise NotImplementedError("This is required")

    def get_tasks_on_active_board(self):
        raise NotImplementedError("This is required")

    def update_task_status(
        self,
        new_task,
        target_position=None,
        append_mode=None,
    ):
        raise NotImplementedError("This is required")
