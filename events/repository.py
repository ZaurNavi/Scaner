from __future__ import annotations
import sqlite3
from datetime import datetime
from typing import List
from storage.archivist.database import DatabaseManager
from .models import Event


def _dt_to_str(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


class EventRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def _get_actual_device_id(self, snapshot_id: str) -> str | None:
        """Получает реальный device_id из snapshot (на случай если bundle содержит старый ID)."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT device_id FROM snapshot WHERE id = ?", (snapshot_id,))
        row = cursor.fetchone()
        return row[0] if row else None

    def save_events(self, events: List[Event]) -> None:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("BEGIN IMMEDIATE")
        try:
            for event in events:
                # Гарантируем, что device_id существует в БД (берём из snapshot)
                actual_device_id = self._get_actual_device_id(event.snapshot_id)
                if actual_device_id is None:
                    continue

                cursor.execute("""
                    INSERT INTO event 
                    (event_id, device_id, snapshot_id, timestamp, type, severity, title, description, details, acknowledged)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.event_id,
                    actual_device_id,
                    event.snapshot_id,
                    _dt_to_str(event.timestamp),
                    event.type.value,
                    event.severity.value,
                    event.title,
                    event.description,
                    event.details,
                    1 if event.acknowledged else 0
                ))
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def get_previous_snapshot(self, device_id: str, current_snapshot_id: str):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        # Получаем реальный device_id из текущего snapshot
        cursor.execute("SELECT device_id FROM snapshot WHERE id = ?", (current_snapshot_id,))
        row = cursor.fetchone()
        if not row:
            return None
        actual_device_id = row[0]

        # Ищем предыдущий snapshot для этого же устройства
        cursor.execute("""
            SELECT id, device_id, ip, hostname, device_type FROM snapshot
            WHERE device_id = ? AND id != ? 
            ORDER BY timestamp DESC 
            LIMIT 1
        """, (actual_device_id, current_snapshot_id))
        row = cursor.fetchone()
        if row:
            return {
                "id": row[0],
                "device_id": row[1],
                "ip": row[2],
                "hostname": row[3],
                "device_type": row[4]
            }
        return None
