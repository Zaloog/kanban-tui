from kanban_tui.database import create_new_task_db, init_new_db


def main():
    init_new_db()
    create_new_task_db(
        title="Test_Task_Ready", description="Hallo", category="Work", column=0
    )
    create_new_task_db(
        title="Test_Task_Ready", description="Hallo", category="Work", column=0
    )
    create_new_task_db(
        title="Test_Task_Doing", description="Hallo", category="Work", column=1
    )
    create_new_task_db(
        title="Test_Task_Done", description="Hallo", category="Work", column=2
    )


if __name__ == "__main__":
    main()
