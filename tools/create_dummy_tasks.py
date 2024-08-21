from kanban_tui.database import create_new_task_db


def main():
    a = create_new_task_db(title="Test_Task", description="Hallo", category="Work")
    print(a)


if __name__ == "__main__":
    main()
