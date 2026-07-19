#!/usr/bin/env python3
"""Database Manager — управление подключением к SQLite."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

# v1.6.9.9: Configuration Layer Integration
from configuration import ConfigurationManager


class DatabaseManager:
    """
    Управляет подключением к SQLite базе данных.
    
    v1.6.9.9: Принимает ConfigurationManager через конструктор (Dependency Injection).
    """
    
    def __init__(
        self,
        db_path: str | Path,
        configuration: Optional[ConfigurationManager] = None
    ):
        self.db_path = Path(db_path)
        self._connection: sqlite3.Connection | None = None
        
        # v1.6.9.9: Configuration через DI
        if configuration is not None:
            self._journal_mode = configuration.get("repository.sqlite.journal_mode", "WAL")
            self._foreign_keys = configuration.get("repository.sqlite.foreign_keys", True)
        else:
            # Fallback на hardcoded значения
            self._journal_mode = "WAL"
            self._foreign_keys = True

    def connect(self) -> sqlite3.Connection:
        if self._connection is None:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._connection = sqlite3.connect(
                str(self.db_path),
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            # Включаем внешние ключи и WAL-режим для производительности и конкурентности
            if self._foreign_keys:
                self._connection.execute("PRAGMA foreign_keys = ON")
            self._connection.execute(f"PRAGMA journal_mode = {self._journal_mode}")
        return self._connection

    def close(self):
        if self._connection:
            self._connection.close()
            self._connection = None

    def get_connection(self) -> sqlite3.Connection:
        return self.connect()
