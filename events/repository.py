from __future__ import annotations
import sqlite3
from datetime import datetime
from typing import List

from storage.archivist.database import DatabaseManager
from .models import Event


def _dt_to_str(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


class EventRepository:
    """Repository для сохранения и чтения событий."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def save_event(self, event: Event) -> None:
        """Сохраняет одно событие."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO event 
            (event_id, device_id, snapshot_id, timestamp, type, severity, title, description, details, acknowledged)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event.event_id,
            event.device_id,
            event.snapshot_id,
            _dt_to_str(event.timestamp),
            event.type.value,
            event.severity.value,
            event.title,
            event.description,
            event.details,
            1 if event.acknowledged else 0,
        ))
        conn.commit()

    def save_events(self, events: List[Event]) -> None:
        """Сохраняет несколько событий в одной транзакции."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("BEGIN IMMEDIATE")
        try:
            for event in events:
                cursor.execute("""
                    INSERT INTO event 
                    (event_id, device_id, snapshot_id, timestamp, type, severity, title, description, details, acknowledged)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.event_id,
                    event.device_id,
                    event.snapshot_id,
                    _dt_to_str(event.timestamp),
                    event.type.value,
                    event.severity.value,
                    event.title,
                    event.description,
                    event.details,
                    1 if event.acknowledged else 0,
                ))
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def get_previous_snapshot(self, device_id: str, current_snapshot_id: str):
        """Возвращает предыдущий Snapshot для устройства (до текущего)."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, scan_id, device_id, timestamp, ip, hostname, os, model, device_type, confidence
            FROM snapshot
            WHERE device_id = ? AND id != ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (device_id, current_snapshot_id))
        row = cursor.fetchone()
        return row if row else None

    def list_events(self, limit: int = 100) -> List[dict]:
        """Возвращает последние события."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT event_id, device_id, snapshot_id, timestamp, type, severity, title, description, details, acknowledged
            FROM event
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        return [
            {
                "event_id": row[0],
                "device_id": row[1],
                "snapshot_id": row[2],
                "timestamp": row[3],
                "type": row[4],
                "severity": row[5],
                "title": row[6],
                "description": row[7],
                "details": row[8],
                "acknowledged": bool(row[9]),
            }
            for row in rows
        ]

    def count_unacknowledged(self) -> int:
        """Возвращает количество неподтвержденных событий."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM event WHERE acknowledged = 0")
        return cursor.fetchone()[0]
