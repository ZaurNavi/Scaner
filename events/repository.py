from __future__ import annotations
import sqlite3
from datetime import datetime
from typing import List, Optional

from storage.archivist.database import DatabaseManager
from .event import Event
from .event_type import EventType, Severity


def _dt_to_str(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def _str_to_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except (ValueError, TypeError):
        return None


class EventRepository:
    """
    Repository для работы с таблицей event.
    Отвечает только за сохранение и чтение событий.
    Не вычисляет события, не знает про Event Engine.
    """

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
            for event in events:
                # Проверяем, не сохранено ли уже это событие (по event_id)
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
            conn.commit()
            return len(events)
        except Exception:
            conn.rollback()
            raise

    def count_unacknowledged(self) -> int:
        """Возвращает количество неподтверждённых событий."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM event WHERE acknowledged = 0")
        return cursor.fetchone()[0]

    def get_events_for_device(self, device_id: str, limit: int = 50) -> List[dict]:
        """Возвращает последние события для устройства."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT event_id, timestamp, type, severity, title, description, details
            FROM event
            WHERE device_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (device_id, limit))
        return [
            {
                "event_id": row[0],
                "timestamp": row[1],
                "type": row[2],
                "severity": row[3],
                "title": row[4],
                "description": row[5],
                "details": row[6],
            }
            for row in cursor.fetchall()
        ]
