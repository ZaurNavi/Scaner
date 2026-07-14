from __future__ import annotations
import sqlite3
from datetime import datetime
from typing import List

from storage.archivist.database import DatabaseManager
from .event import Event


def _dt_to_str(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


class EventRepository:
    """Repository для работы с таблицей event."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def save_events(self, events: List[Event]) -> int:
        """
        Сохраняет список событий в БД.
        Возвращает количество сохранённых событий.
        """
        if not events:
            return 0

        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("BEGIN IMMEDIATE")
        try:
            saved = 0
            for event in events:
                # Проверяем, не сохранено ли уже это событие
                cursor.execute("SELECT 1 FROM event WHERE event_id = ?", (event.event_id,))
                if cursor.fetchone():
                    continue  # Пропускаем дубликаты

                cursor.execute("""
                    INSERT INTO event 
                    (event_id, device_id, snapshot_id, timestamp, type, severity, 
                     title, description, details, acknowledged)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.event_id,
                    event.device_id,
                    "",  # snapshot_id пока не используем
                    _dt_to_str(event.timestamp),
                    event.type.value,
                    event.severity.value,
                    event.title,
                    event.description,
                    f"{event.old_value} → {event.new_value}" if event.old_value or event.new_value else "",
                    1 if event.acknowledged else 0,
                ))
                saved += 1
            conn.commit()
            return saved
        except Exception as e:
            conn.rollback()
            print(f"      [ERROR] Failed to save events: {e}")
            return 0
