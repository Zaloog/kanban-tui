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
        title="Task_green_ready", description="Hallo", category="green", column="Ready"
    )
    create_new_task_db(
        title="Task_blue_ready", description="Hallo", category="blue", column="Ready"
    )
    create_new_task_db(
        title="Task_none_ready", description="Hallo", category=None, column="Ready"
    )

    # Doing
    create_new_task_db(
        title="Task_green_doing", description="Hallo", category="green", column="Doing"
    )
    # Done
    create_new_task_db(
        title="Task_red_done", description="Hallo", category="red", column="Done"
    )


if __name__ == "__main__":
    main()
