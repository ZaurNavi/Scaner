import sqlite3
from pathlib import Path

class DatabaseManager:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self._connection: sqlite3.Connection | None = None

    def connect(self) -> sqlite3.Connection:
        if self._connection is None:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._connection = sqlite3.connect(
                str(self.db_path),
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            # Включаем внешние ключи и WAL-режим для производительности и конкурентности
            self._connection.execute("PRAGMA foreign_keys = ON")
            self._connection.execute("PRAGMA journal_mode = WAL")
        return self._connection

    def close(self):
        if self._connection:
            self._connection.close()
            self._connection = None

    def get_connection(self) -> sqlite3.Connection:
        return self.connect()
