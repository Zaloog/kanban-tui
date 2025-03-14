import pytest
from datetime import datetime
from kanban_tui.utils import (
    calculate_work_on_time,
    get_days_left_till_due,
    get_time_range,
    get_status_enum,
)

from freezegun import freeze_time


@pytest.mark.parametrize(
    "test_start, test_finish, test_time_start, test_time_finish, expected_result",
    [
        # start inside limit, end inside limit next 2 days
        (
            datetime(year=2024, month=7, day=6, hour=15, minute=0, second=0),
            datetime(year=2024, month=7, day=8, hour=9, minute=0, second=0),
            "08:00",
            "16:00",
            2 * 60 + 8 * 60,
        ),
        # start inside limit, end inside limit next day
        (
            datetime(year=2024, month=7, day=6, hour=15, minute=0, second=0),
            datetime(year=2024, month=7, day=7, hour=9, minute=0, second=0),
            "08:00",
            "16:00",
            2 * 60,
        ),
        # start inside limit, end inside limit same day
        (
            datetime(year=2024, month=7, day=6, hour=9, minute=0, second=0),
            datetime(year=2024, month=7, day=6, hour=11, minute=0, second=0),
            "08:00",
            "16:00",
            2 * 60,
        ),
        # start before start_limit, end inside limit same day
        (
            datetime(year=2024, month=7, day=6, hour=7, minute=0, second=0),
            datetime(year=2024, month=7, day=6, hour=9, minute=0, second=0),
            "08:00",
            "16:00",
            2 * 60,
        ),
        # start before start_limit, end inside limit next day
        (
            datetime(year=2024, month=7, day=6, hour=7, minute=0, second=0),
            datetime(year=2024, month=7, day=7, hour=9, minute=0, second=0),
            "08:00",
            "16:00",
            9 * 60 + 1 * 60,
        ),
        # start before start_limit, end after end_limit same day
        (
            datetime(year=2024, month=7, day=7, hour=7, minute=0, second=0),
            datetime(year=2024, month=7, day=7, hour=17, minute=0, second=0),
            "08:00",
            "16:00",
            10 * 60,
        ),
        # Always count the whole time
        (
            datetime(year=2024, month=7, day=6, hour=12, minute=0, second=0),
            datetime(year=2024, month=7, day=7, hour=12, minute=0, second=0),
            "00:00",
            "00:00",
            1440,
        ),
    ],
)
def test_calculate_work_on_time(
    test_start, test_finish, test_time_start, test_time_finish, expected_result
):
    workon_time = calculate_work_on_time(
        test_start, test_finish, test_time_start, test_time_finish
    )

    assert workon_time == expected_result


@pytest.mark.parametrize(
    "due_date, expected_result",
    [
        ("2024-01-06T00:00:00", 1),
        ("2024-01-02T00:00:00", 0),
        ("2024-01-20T00:00:00", 15),
        (None, None),
    ],
)
def test_get_days_left_till_due(due_date, expected_result):
    with freeze_time(datetime(year=2024, month=1, day=5, hour=0, minute=0, second=1)):
        calculated_days = get_days_left_till_due(due_date=due_date)

        assert calculated_days == expected_result


@pytest.mark.parametrize(
    "test_start, test_end, frequency, expected_result",
    [
        # start inside limit, end inside limit next 2 days
        (
            datetime(year=2024, month=7, day=1),
            datetime(year=2024, month=7, day=2),
            "day",
            2,
        ),
        (
            datetime(year=2024, month=7, day=1),
            datetime(year=2024, month=9, day=1),
            "day",
            63,
        ),
        (
            datetime(year=2024, month=1, day=1),
            datetime(year=2025, month=1, day=1),
            "day",
            367,
        ),
        (
            datetime(year=2024, month=7, day=1),
            datetime(year=2024, month=7, day=2),
            "month",
            1,
        ),
        (
            datetime(year=2024, month=7, day=1),
            datetime(year=2024, month=12, day=1),
            "month",
            6,
        ),
        (
            datetime(year=2024, month=4, day=1),
            datetime(year=2025, month=8, day=1),
            "month",
            17,
        ),
        (
            datetime(year=2024, month=7, day=1),
            datetime(year=2024, month=7, day=2),
            "week",
            1,
        ),
        (
            datetime(year=2024, month=7, day=1),
            datetime(year=2024, month=8, day=15),
            "week",
            7,
        ),
        (
            datetime(year=2024, month=4, day=1),
            datetime(year=2025, month=8, day=1),
            "week",
            70,
        ),
    ],
)
def test_get_time_range(test_start, test_end, frequency, expected_result):
    delta = get_time_range(interval=frequency, start=test_start, end=test_end)

    assert len(delta) == expected_result


def test_get_status_enum():
    status_enum = get_status_enum(
        reset=None,
        start=1,
        finish=2,
    )
    assert status_enum.RESET.value is None
    assert status_enum.START.value == 1
    assert status_enum.FINISH.value == 2
