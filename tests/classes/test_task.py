from kanban_tui.classes.task import Task
from datetime import datetime, timedelta


def test_Task():
    test_task = Task(
        task_id=1337,
        title="Test_Task",
        column="Ready",
        due_date=datetime.now() + timedelta(days=7),
    )

    assert test_task.column == "Ready"
    assert test_task.days_left == 8
    test_task.start_task()
    assert test_task.start_date == datetime.now().replace(microsecond=0)

    test_task.start_date = datetime.now() - timedelta(days=10)
    assert test_task.finished is False

    test_task.finish_task()

    assert test_task.finished
    assert test_task.time_worked_on == 10 * 24 * 60

    test_task.due_date = None
    test_task.get_days_left_till_due() is None


def test_finished_Task():
    test_task_finished = Task(
        task_id=1337,
        title="Test_Task",
        column="Done",
        start_date=datetime.now() - timedelta(days=10),
        finish_date=datetime.now(),
    )

    assert test_task_finished.column == "Done"
    assert test_task_finished.finished


def test_move_Task():
    test_task_moved = Task(
        task_id=1337,
        title="Test_Task",
        column="Ready",
        due_date=datetime.now() + timedelta(days=7),
    )

    assert test_task_moved.start_date is None
    assert test_task_moved.finish_date is None

    test_task_moved.update_task_status(new_column="Doing")
    test_task_moved.column = "Doing"
    assert test_task_moved.start_date == datetime.now().replace(microsecond=0)
    assert test_task_moved.finish_date is None
    assert test_task_moved.column == "Doing"

    test_task_moved.update_task_status(new_column="Done")
    test_task_moved.column = "Done"
    assert test_task_moved.finish_date == datetime.now().replace(microsecond=0)
    assert test_task_moved.column == "Done"

    test_task_moved.update_task_status(new_column="Ready")
    test_task_moved.column = "Ready"
    assert test_task_moved.start_date is None
    assert test_task_moved.finish_date is None
    assert test_task_moved.column == "Ready"
