from pathlib import Path

COLUMNS = ["Ready", "Doing", "Done"]

COLUMN_DICT = {column_name: idx for idx, column_name in enumerate(COLUMNS)}

DB_NAME = "database.db"
DB_LOCATION = Path().cwd()
DB_FULL_PATH = DB_LOCATION / DB_NAME
