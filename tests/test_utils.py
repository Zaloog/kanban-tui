import pytest
from datetime import datetime
from kanban_tui.utils import calculate_work_on_time


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
