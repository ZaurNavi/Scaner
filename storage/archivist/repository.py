from __future__ import annotations
import sqlite3
from datetime import datetime
from .database import DatabaseManager
from storage.schema import SnapshotBundle


def _dt_to_str(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


class Repository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def save_bundle(self, bundle: SnapshotBundle) -> None:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("BEGIN IMMEDIATE")

            # 1. Сохраняем Scan (INSERT OR IGNORE)
            if bundle.scan:
                cursor.execute("""
                    INSERT OR IGNORE INTO scan 
                    (id, started_at, finished_at, collector_version, duration_ms, devices_found, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    bundle.scan.id,
                    _dt_to_str(bundle.scan.started_at),
                    _dt_to_str(bundle.scan.finished_at),
                    bundle.scan.collector_version,
                    bundle.scan.duration_ms,
                    bundle.scan.devices_found,
                    bundle.scan.status.value
                ))

            # 2. Сохраняем/Обновляем Device и получаем ПРАВИЛЬНЫЙ device_id
            actual_device_id = bundle.snapshot.device_id  # По умолчанию берем из bundle
            
            if bundle.device:
                # Проверяем, существует ли уже устройство с таким MAC
                cursor.execute("SELECT id FROM device WHERE mac = ?", (bundle.device.mac,))
                existing = cursor.fetchone()
                
                if existing:
                    # Устройство уже есть: используем его ID и обновляем last_seen
                    actual_device_id = existing[0]
                    cursor.execute("""
                        UPDATE device SET last_seen = ?, status = ? WHERE id = ?
                    """, (
                        _dt_to_str(bundle.device.last_seen),
                        bundle.device.status.value,
                        actual_device_id
                    ))
                else:
                    # Устройство новое: вставляем его с новым ID
                    actual_device_id = bundle.device.id
                    cursor.execute("""
                        INSERT INTO device (id, mac, first_seen, last_seen, status)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        actual_device_id,
                        bundle.device.mac,
                        _dt_to_str(bundle.device.first_seen),
                        _dt_to_str(bundle.device.last_seen),
                        bundle.device.status.value
                    ))

            # 3. Сохраняем Snapshot (используем actual_device_id!)
            cursor.execute("""
                INSERT INTO snapshot 
                (id, scan_id, device_id, timestamp, ip, hostname, os, model, device_type, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                bundle.snapshot.id,
                bundle.scan_id,
                actual_device_id,  # <--- ИСПРАВЛЕНИЕ: гарантированно существующий ID
                _dt_to_str(bundle.snapshot.timestamp),
                bundle.snapshot.ip,
                bundle.snapshot.hostname,
                bundle.snapshot.os,
                bundle.snapshot.model,
                bundle.snapshot.device_type.value,
                bundle.snapshot.confidence
            ))

            # 4. Сохраняем Observations
            for obs in bundle.observations:
                cursor.execute("""
                    INSERT INTO observation 
                    (id, snapshot_id, source, key, value, obs_type, unit, confidence)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    obs.id, obs.snapshot_id, obs.source.value, obs.key, obs.value,
                    obs.obs_type.value, obs.unit, obs.confidence
                ))

            # 5. Сохраняем Evidence
            for ev in bundle.evidence:
                cursor.execute("""
                    INSERT INTO evidence 
                    (id, snapshot_id, description, contribution, source, details)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    ev.id, ev.snapshot_id, ev.description, ev.contribution,
                    ev.source.value, ev.details
                ))

            # 6. Сохраняем Capabilities
            for cap in bundle.capabilities:
                cursor.execute("""
                    INSERT INTO capability 
                    (id, snapshot_id, capability, confidence)
                    VALUES (?, ?, ?, ?)
                """, (
                    cap.id, cap.snapshot_id, cap.capability.value, cap.confidence
                ))

            # 7. Сохраняем CollectorLog
            if bundle.collector_log:
                cursor.execute("""
                    INSERT INTO collector_log 
                    (id, scan_id, collector_name, started_at, finished_at, duration_ms, 
                     objects_processed, status, warnings, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    bundle.collector_log.id, bundle.collector_log.scan_id,
                    bundle.collector_log.collector_name,
                    _dt_to_str(bundle.collector_log.started_at),
                    _dt_to_str(bundle.collector_log.finished_at),
                    bundle.collector_log.duration_ms,
                    bundle.collector_log.objects_processed,
                    bundle.collector_log.status.value,
                    bundle.collector_log.warnings,
                    bundle.collector_log.error_message
                ))

            conn.commit()
        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Failed to save SnapshotBundle: {e}")
