from datetime import datetime, timedelta
from kanban_tui.database import create_new_task_db, init_new_db
from kanban_tui.config import KanbanTuiConfig, init_new_config

from kanban_tui.constants import DB_FULL_PATH, CONFIG_FULL_PATH


def main():
    CONFIG_FULL_PATH.unlink(missing_ok=True)
    init_new_config()

    cfg = KanbanTuiConfig()

    cfg.add_category(
        category="green",
        color="#00FF00",
    )
    cfg.add_category(
        category="blue",
        color="#0000FF",
    )
    cfg.add_category(
        category="red",
        color="#FF0000",
    )

    DB_FULL_PATH.unlink(missing_ok=True)
    init_new_db()
    # Ready
    create_new_task_db(
        title="Task_green_ready",
        description="First Task",
        category="green",
        column="Ready",
        due_date=datetime.now(),
    )
    create_new_task_db(
        title="Task_blue_ready",
        description="Second Task",
        category="blue",
        column="Ready",
        due_date=datetime.now() + timedelta(days=1),
    )
    create_new_task_db(
        title="Task_none_ready",
        description="Third Task",
        category=None,
        column="Ready",
        due_date=datetime.now() + timedelta(days=3),
    )

    # Doing
    create_new_task_db(
        title="Task_green_doing",
        description="Task I am working on",
        category="green",
        column="Doing",
    )
    # Done
    create_new_task_db(
        title="Task_red_done",
        description="Task Finished",
        category="red",
        column="Done",
        start_date=datetime(year=2024, month=3, day=16, hour=12, minute=30),
        finish_date=datetime(year=2024, month=3, day=18, hour=12, minute=30),
    )
    # Archive
    for month in range(5, 10):
        create_new_task_db(
            title="Task_red_archive",
            description="Hallo",
            category="red",
            column="Archive",
            start_date=datetime(year=2024, month=month, day=13, hour=12, minute=30),
            finish_date=datetime(year=2024, month=month, day=14, hour=12, minute=30),
        )
    for day in range(20, 25):
        create_new_task_db(
            title="Task_red_archive",
            description="Hallo",
            category="red",
            column="Archive",
            start_date=datetime(year=2024, month=8, day=day, hour=12, minute=30),
            finish_date=datetime(year=2024, month=9, day=day, hour=12, minute=30),
        )


if __name__ == "__main__":
    main()
