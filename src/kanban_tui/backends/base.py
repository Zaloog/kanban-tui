class Backend:
    """Base Backend Class"""

    def get_boards(self):
        raise NotImplementedError("This is required")

    def get_columns(self):
        raise NotImplementedError("This is required")

    def get_tasks(self):
        raise NotImplementedError("This is required")
