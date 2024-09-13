from datetime import datetime
from kanban_tui.database import create_new_task_db, init_new_db
from kanban_tui.config import KanbanTuiConfig, init_new_config

from kanban_tui.constants import DB_FULL_PATH, CONFIG_FULL_PATH


def main():
    CONFIG_FULL_PATH.unlink(missing_ok=True)
    init_new_config()

    cfg = KanbanTuiConfig()

    cfg.add_category(
        category="blue",
        color="#0000FF",
    )
    cfg.add_category(
        category="red",
        color="#FF0000",
    )
    cfg.add_category(
        category="green",
        color="#00FF00",
    )

    DB_FULL_PATH.unlink(missing_ok=True)
    init_new_db()
    # Ready
    create_new_task_db(
        title="Task_green_ready",
        description="Hallo",
        category="green",
        column="Ready",
        start_date=datetime(year=2024, month=1, day=15, hour=12, minute=30),
    )
    create_new_task_db(
        title="Task_blue_ready",
        description="Hallo",
        category="blue",
        column="Ready",
        start_date=datetime(year=2024, month=1, day=15, hour=12, minute=30),
    )
    create_new_task_db(
        title="Task_none_ready",
        description="Hallo",
        category=None,
        column="Ready",
        start_date=datetime(year=2024, month=1, day=15, hour=12, minute=30),
    )

    # Doing
    create_new_task_db(
        title="Task_green_doing",
        description="Hallo",
        category="green",
        column="Doing",
        start_date=datetime(year=2024, month=2, day=15, hour=12, minute=30),
    )
    # Done
    create_new_task_db(
        title="Task_red_done",
        description="Hallo",
        category="red",
        column="Done",
        start_date=datetime(year=2024, month=3, day=15, hour=12, minute=30),
    )
    # Archive
    for month in range(1, 12):
        create_new_task_db(
            title="Task_red_done",
            description="Hallo",
            category="red",
            column="Archive",
            start_date=datetime(year=2024, month=month, day=15, hour=12, minute=30),
        )
    create_new_task_db(
        title="Future Task",
        description="Hallo",
        category=None,
        column="Archive",
        start_date=datetime(year=2025, month=1, day=15, hour=12, minute=30),
    )


if __name__ == "__main__":
    main()
