from pathlib import Path

COLUMNS = ["Ready", "Doing", "Done"]

COLUMN_DICT = {column_name: idx for idx, column_name in enumerate(COLUMNS)}

DB_NAME = "database.db"
DB_LOCATION = Path().cwd()
DB_FULL_PATH = DB_LOCATION / DB_NAME

CONFIG_NAME = "kanban_tui.ini"
CONFIG_LOCATION = Path().cwd()
CONFIG_FULL_PATH = CONFIG_LOCATION / CONFIG_NAME


EXAMPLE_MARKDOWN = """# Markdown Document

This is an example of Textual's `Markdown` widget.

## Features

- Syntax highlighted code blocks
- Tables!
"""
