from __future__ import annotations
from typing import Literal, Any
from enum import Enum

import re
from pathlib import Path
from datetime import datetime, timedelta
from dateutil.rrule import rrule, MONTHLY, WEEKLY, DAILY
from functools import lru_cache

from kanban_tui.database import create_new_task_db, init_new_db, create_new_board_db
from kanban_tui.config import KanbanTuiConfig, init_new_config


def get_status_enum(reset: int | None, start: int | None, finish: int | None) -> Enum:
    return Enum("StatusEnum", [("RESET", reset), ("START", start), ("FINISH", finish)])


@lru_cache
def getrgb(color: str) -> tuple[int, int, int] | tuple[int, int, int, int]:
    #
    # The Python Imaging Library
    # $Id$
    #
    # map CSS3-style colour description strings to RGB
    #
    # History:
    # 2002-10-24 fl   Added support for CSS-style color strings
    # 2002-12-15 fl   Added RGBA support
    # 2004-03-27 fl   Fixed remaining int() problems for Python 1.5.2
    # 2004-07-19 fl   Fixed gray/grey spelling issues
    # 2009-03-05 fl   Fixed rounding error in grayscale calculation
    #
    # Copyright (c) 2002-2004 by Secret Labs AB
    # Copyright (c) 2002-2004 by Fredrik Lundh
    #
    # Licence Info

    # The Python Imaging Library (PIL) is

    #     Copyright © 1997-2011 by Secret Labs AB
    #     Copyright © 1995-2011 by Fredrik Lundh and contributors

    # Pillow is the friendly PIL fork. It is

    #     Copyright © 2010-2024 by Jeffrey A. Clark and contributors

    # Like PIL, Pillow is licensed under the open source HPND License:

    # By obtaining, using, and/or copying this software and/or its associated
    # documentation, you agree that you have read, understood, and will comply
    # with the following terms and conditions:

    # Permission to use, copy, modify and distribute this software and its
    # documentation for any purpose and without fee is hereby granted,
    # provided that the above copyright notice appears in all copies, and that
    # both that copyright notice and this permission notice appear in supporting
    # documentation, and that the name of Secret Labs AB or the author not be
    # used in advertising or publicity pertaining to distribution of the software
    # without specific, written prior permission.

    # SECRET LABS AB AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS
    # SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS.
    # IN NO EVENT SHALL SECRET LABS AB OR THE AUTHOR BE LIABLE FOR ANY SPECIAL,
    # INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
    # LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE
    # OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
    # PERFORMANCE OF THIS SOFTWARE.
    """
     Convert a color string to an RGB or RGBA tuple. If the string cannot be
     parsed, this function raises a :py:exc:`ValueError` exception.

    .. versionadded:: 1.1.4

    :param color: A color string
    :return: ``(red, green, blue[, alpha])``
    """
    if len(color) > 100:
        msg = "color specifier is too long"
        raise ValueError(msg)
    color = color.lower()

    rgb = colormap.get(color, None)
    if rgb:
        if isinstance(rgb, tuple):
            return rgb
        rgb_tuple = getrgb(rgb)
        assert len(rgb_tuple) == 3
        colormap[color] = rgb_tuple
        return rgb_tuple

    # check for known string formats
    if re.match("#[a-f0-9]{3}$", color):
        return int(color[1] * 2, 16), int(color[2] * 2, 16), int(color[3] * 2, 16)

    if re.match("#[a-f0-9]{4}$", color):
        return (
            int(color[1] * 2, 16),
            int(color[2] * 2, 16),
            int(color[3] * 2, 16),
            int(color[4] * 2, 16),
        )

    if re.match("#[a-f0-9]{6}$", color):
        return int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)

    if re.match("#[a-f0-9]{8}$", color):
        return (
            int(color[1:3], 16),
            int(color[3:5], 16),
            int(color[5:7], 16),
            int(color[7:9], 16),
        )

    m = re.match(r"rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)$", color)
    if m:
        return int(m.group(1)), int(m.group(2)), int(m.group(3))

    m = re.match(r"rgb\(\s*(\d+)%\s*,\s*(\d+)%\s*,\s*(\d+)%\s*\)$", color)
    if m:
        return (
            int((int(m.group(1)) * 255) / 100.0 + 0.5),
            int((int(m.group(2)) * 255) / 100.0 + 0.5),
            int((int(m.group(3)) * 255) / 100.0 + 0.5),
        )

    m = re.match(
        r"hsl\(\s*(\d+\.?\d*)\s*,\s*(\d+\.?\d*)%\s*,\s*(\d+\.?\d*)%\s*\)$", color
    )
    if m:
        from colorsys import hls_to_rgb

        rgb_floats = hls_to_rgb(
            float(m.group(1)) / 360.0,
            float(m.group(3)) / 100.0,
            float(m.group(2)) / 100.0,
        )
        return (
            int(rgb_floats[0] * 255 + 0.5),
            int(rgb_floats[1] * 255 + 0.5),
            int(rgb_floats[2] * 255 + 0.5),
        )

    m = re.match(
        r"hs[bv]\(\s*(\d+\.?\d*)\s*,\s*(\d+\.?\d*)%\s*,\s*(\d+\.?\d*)%\s*\)$", color
    )
    if m:
        from colorsys import hsv_to_rgb

        rgb_floats = hsv_to_rgb(
            float(m.group(1)) / 360.0,
            float(m.group(2)) / 100.0,
            float(m.group(3)) / 100.0,
        )
        return (
            int(rgb_floats[0] * 255 + 0.5),
            int(rgb_floats[1] * 255 + 0.5),
            int(rgb_floats[2] * 255 + 0.5),
        )

    m = re.match(r"rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)$", color)
    if m:
        return int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
    msg = f"unknown color specifier: {repr(color)}"
    raise ValueError(msg)


colormap: dict[str, str | tuple[int, int, int]] = {
    # X11 colour table from https://drafts.csswg.org/css-color-4/, with
    # gray/grey spelling issues fixed.  This is a superset of HTML 4.0
    # colour names used in CSS 1.
    "aliceblue": "#f0f8ff",
    "antiquewhite": "#faebd7",
    "aqua": "#00ffff",
    "aquamarine": "#7fffd4",
    "azure": "#f0ffff",
    "beige": "#f5f5dc",
    "bisque": "#ffe4c4",
    "black": "#000000",
    "blanchedalmond": "#ffebcd",
    "blue": "#0000ff",
    "blueviolet": "#8a2be2",
    "brown": "#a52a2a",
    "burlywood": "#deb887",
    "cadetblue": "#5f9ea0",
    "chartreuse": "#7fff00",
    "chocolate": "#d2691e",
    "coral": "#ff7f50",
    "cornflowerblue": "#6495ed",
    "cornsilk": "#fff8dc",
    "crimson": "#dc143c",
    "cyan": "#00ffff",
    "darkblue": "#00008b",
    "darkcyan": "#008b8b",
    "darkgoldenrod": "#b8860b",
    "darkgray": "#a9a9a9",
    "darkgrey": "#a9a9a9",
    "darkgreen": "#006400",
    "darkkhaki": "#bdb76b",
    "darkmagenta": "#8b008b",
    "darkolivegreen": "#556b2f",
    "darkorange": "#ff8c00",
    "darkorchid": "#9932cc",
    "darkred": "#8b0000",
    "darksalmon": "#e9967a",
    "darkseagreen": "#8fbc8f",
    "darkslateblue": "#483d8b",
    "darkslategray": "#2f4f4f",
    "darkslategrey": "#2f4f4f",
    "darkturquoise": "#00ced1",
    "darkviolet": "#9400d3",
    "deeppink": "#ff1493",
    "deepskyblue": "#00bfff",
    "dimgray": "#696969",
    "dimgrey": "#696969",
    "dodgerblue": "#1e90ff",
    "firebrick": "#b22222",
    "floralwhite": "#fffaf0",
    "forestgreen": "#228b22",
    "fuchsia": "#ff00ff",
    "gainsboro": "#dcdcdc",
    "ghostwhite": "#f8f8ff",
    "gold": "#ffd700",
    "goldenrod": "#daa520",
    "gray": "#808080",
    "grey": "#808080",
    "green": "#008000",
    "greenyellow": "#adff2f",
    "honeydew": "#f0fff0",
    "hotpink": "#ff69b4",
    "indianred": "#cd5c5c",
    "indigo": "#4b0082",
    "ivory": "#fffff0",
    "khaki": "#f0e68c",
    "lavender": "#e6e6fa",
    "lavenderblush": "#fff0f5",
    "lawngreen": "#7cfc00",
    "lemonchiffon": "#fffacd",
    "lightblue": "#add8e6",
    "lightcoral": "#f08080",
    "lightcyan": "#e0ffff",
    "lightgoldenrodyellow": "#fafad2",
    "lightgreen": "#90ee90",
    "lightgray": "#d3d3d3",
    "lightgrey": "#d3d3d3",
    "lightpink": "#ffb6c1",
    "lightsalmon": "#ffa07a",
    "lightseagreen": "#20b2aa",
    "lightskyblue": "#87cefa",
    "lightslategray": "#778899",
    "lightslategrey": "#778899",
    "lightsteelblue": "#b0c4de",
    "lightyellow": "#ffffe0",
    "lime": "#00ff00",
    "limegreen": "#32cd32",
    "linen": "#faf0e6",
    "magenta": "#ff00ff",
    "maroon": "#800000",
    "mediumaquamarine": "#66cdaa",
    "mediumblue": "#0000cd",
    "mediumorchid": "#ba55d3",
    "mediumpurple": "#9370db",
    "mediumseagreen": "#3cb371",
    "mediumslateblue": "#7b68ee",
    "mediumspringgreen": "#00fa9a",
    "mediumturquoise": "#48d1cc",
    "mediumvioletred": "#c71585",
    "midnightblue": "#191970",
    "mintcream": "#f5fffa",
    "mistyrose": "#ffe4e1",
    "moccasin": "#ffe4b5",
    "navajowhite": "#ffdead",
    "navy": "#000080",
    "oldlace": "#fdf5e6",
    "olive": "#808000",
    "olivedrab": "#6b8e23",
    "orange": "#ffa500",
    "orangered": "#ff4500",
    "orchid": "#da70d6",
    "palegoldenrod": "#eee8aa",
    "palegreen": "#98fb98",
    "paleturquoise": "#afeeee",
    "palevioletred": "#db7093",
    "papayawhip": "#ffefd5",
    "peachpuff": "#ffdab9",
    "peru": "#cd853f",
    "pink": "#ffc0cb",
    "plum": "#dda0dd",
    "powderblue": "#b0e0e6",
    "purple": "#800080",
    "rebeccapurple": "#663399",
    "red": "#ff0000",
    "rosybrown": "#bc8f8f",
    "royalblue": "#4169e1",
    "saddlebrown": "#8b4513",
    "salmon": "#fa8072",
    "sandybrown": "#f4a460",
    "seagreen": "#2e8b57",
    "seashell": "#fff5ee",
    "sienna": "#a0522d",
    "silver": "#c0c0c0",
    "skyblue": "#87ceeb",
    "slateblue": "#6a5acd",
    "slategray": "#708090",
    "slategrey": "#708090",
    "snow": "#fffafa",
    "springgreen": "#00ff7f",
    "steelblue": "#4682b4",
    "tan": "#d2b48c",
    "teal": "#008080",
    "thistle": "#d8bfd8",
    "tomato": "#ff6347",
    "turquoise": "#40e0d0",
    "violet": "#ee82ee",
    "wheat": "#f5deb3",
    "white": "#ffffff",
    "whitesmoke": "#f5f5f5",
    "yellow": "#ffff00",
    "yellowgreen": "#9acd32",
}


def calculate_work_on_time(
    start_date: datetime,
    finish_date: datetime,
    start_work: str,
    finish_work: str,
):
    if start_work == finish_work:
        return (finish_date - start_date) / timedelta(minutes=1)

    workon_time = 0
    start_hours, start_minutes = (int(time) for time in start_work.split(":"))
    end_hours, end_minutes = (int(time) for time in finish_work.split(":"))
    delta_days = (finish_date.date() - start_date.date()).days

    start_limit = start_date.replace(
        hour=start_hours, minute=start_minutes, second=0, microsecond=0
    )

    # End is next day
    if end_hours < start_hours:
        end_limit_start = start_date.replace(
            day=start_date.day + 1,
            hour=end_hours,
            minute=end_minutes,
            second=0,
            microsecond=0,
        )
    else:
        end_limit_start = start_date.replace(
            hour=end_hours, minute=end_minutes, second=0, microsecond=0
        )

    if delta_days < 1:
        workon_time += (finish_date - start_date) // timedelta(minutes=1)
    else:
        for day in range(0, delta_days + 1):
            # first day
            if day == 0:
                workon_time += (end_limit_start - start_date) // timedelta(minutes=1)
            # last day
            elif day == delta_days:
                workon_time += (
                    finish_date - start_limit.replace(day=finish_date.day)
                ) // timedelta(minutes=1)
            # between days
            else:
                workon_time += (end_limit_start - start_limit) // timedelta(minutes=1)

    return workon_time


def create_demo_tasks(database_path: Path, config_path: Path):
    init_new_config(config_path=config_path, database=database_path)

    cfg = KanbanTuiConfig(config_path=config_path)

    cfg.add_category(
        category="green",
        color="#008F00",
    )
    cfg.add_category(
        category="blue",
        color="#00008F",
    )
    cfg.add_category(
        category="red",
        color="#8F0000",
    )

    init_new_db(database=database_path)

    # Create 2 Demo Boards
    create_new_board_db(
        name="Demo Board No1", icon=":construction:", database=database_path
    )
    create_new_board_db(
        name="Demo Board No2", icon=":sparkles:", database=database_path
    )
    for i in range(3, 6):
        create_new_board_db(
            name=f"Demo Board No{i}", icon=":sparkles:", database=database_path
        )

    # Ready
    create_new_task_db(
        title="Task_green_ready",
        description="First Task",
        category="green",
        column=1,
        due_date=datetime.now(),
        board_id=cfg.active_board,
        database=database_path,
    )
    create_new_task_db(
        title="Task_blue_ready",
        description="Second Task",
        category="blue",
        column=1,
        due_date=datetime.now() + timedelta(days=1),
        board_id=cfg.active_board,
        database=database_path,
    )
    create_new_task_db(
        title="Task_none_ready",
        description="Third Task",
        category=None,
        column=1,
        due_date=datetime.now() + timedelta(days=3),
        board_id=cfg.active_board,
        database=database_path,
    )

    # Doing
    create_new_task_db(
        title="Task_green_doing",
        description="Task I am working on",
        category="green",
        column=2,
        start_date=datetime.now(),
        board_id=cfg.active_board,
        database=database_path,
    )
    # Done
    create_new_task_db(
        title="Task_red_done",
        description="Task Finished",
        category="red",
        column=3,
        start_date=datetime(year=2024, month=3, day=16, hour=12, minute=30),
        finish_date=datetime(year=2024, month=3, day=18, hour=12, minute=30),
        board_id=cfg.active_board,
        database=database_path,
    )
    # Archive
    for month in range(5, 10):
        create_new_task_db(
            title="Task_red_archive",
            description="Hallo",
            category="red",
            column=4,
            start_date=datetime(year=2024, month=month, day=13, hour=12, minute=30),
            finish_date=datetime(year=2024, month=month, day=14, hour=12, minute=30),
            board_id=cfg.active_board,
            database=database_path,
        )
    for day in range(20, 25):
        create_new_task_db(
            title="Task_red_archive",
            description="Hallo",
            category="red",
            column=4,
            start_date=datetime(year=2024, month=8, day=day, hour=12, minute=30),
            finish_date=datetime(year=2024, month=9, day=day, hour=12, minute=30),
            board_id=cfg.active_board,
            database=database_path,
        )


def get_days_left_till_due(due_date: str | None):
    if due_date is not None:
        due_date_date = datetime.fromisoformat(due_date)
        return max(
            0,
            (due_date_date - datetime.now().replace(microsecond=0)) // timedelta(days=1)
            + 1,
        )
    return None


def get_time_range(
    interval: Literal["day", "week", "month"], start: datetime, end: datetime
) -> list[Any]:
    match interval:
        case "day":
            return list(rrule(freq=DAILY, dtstart=start, until=end))
        case "week":
            return list(rrule(freq=WEEKLY, dtstart=start, until=end))
        case "month":
            # Still a bit buggy
            # doesn't show task for jan25 when color hue is active
            return list(rrule(freq=MONTHLY, dtstart=start, until=end))
