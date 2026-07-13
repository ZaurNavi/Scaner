from __future__ import annotations
import sqlite3
import time
from datetime import datetime
from typing import List, Tuple
from .database import DatabaseManager
from storage.schema import SnapshotBundle, SaveResult, Snapshot


def _dt_to_str(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


class Repository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def save_bundle(self, bundle: SnapshotBundle) -> SaveResult:
        """
        Сохраняет SnapshotBundle и возвращает SaveResult с детальной статистикой.
        """
        start_time = time.time()
        result = SaveResult()
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("BEGIN IMMEDIATE")

            # 1. Scan (INSERT OR IGNORE)
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

            # 2. Device (UPSERT — создаём или обновляем last_seen)
            if bundle.device:
                cursor.execute("SELECT id FROM device WHERE mac = ?", (bundle.device.mac,))
                existing = cursor.fetchone()
                
                if existing:
                    # Устройство уже есть — обновляем last_seen
                    cursor.execute("""
                        UPDATE device SET last_seen = ?, status = ? WHERE id = ?
                    """, (
                        _dt_to_str(bundle.device.last_seen),
                        bundle.device.status.value,
                        existing[0]
                    ))
                    result = SaveResult(
                        devices_updated=1,
                        snapshots_saved=result.snapshots_saved,
                        observations_saved=result.observations_saved,
                        evidence_saved=result.evidence_saved,
                        capabilities_saved=result.capabilities_saved,
                        sessions_updated=result.sessions_updated,
                        elapsed_ms=result.elapsed_ms,
                        success=result.success,
                        error_message=result.error_message,
                    )
                    actual_device_id = existing[0]
                else:
                    # Устройство новое — создаём
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
                    result = SaveResult(
                        devices_created=1,
                        snapshots_saved=result.snapshots_saved,
                        observations_saved=result.observations_saved,
                        evidence_saved=result.evidence_saved,
                        capabilities_saved=result.capabilities_saved,
                        sessions_updated=result.sessions_updated,
                        elapsed_ms=result.elapsed_ms,
                        success=result.success,
                        error_message=result.error_message,
                    )
            else:
                actual_device_id = bundle.snapshot.device_id if bundle.snapshot else None

            # 3. Snapshot
            if bundle.snapshot:
                cursor.execute("""
                    INSERT INTO snapshot 
                    (id, scan_id, device_id, timestamp, ip, hostname, os, model, device_type, confidence)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    bundle.snapshot.id,
                    bundle.scan_id,
                    actual_device_id,
                    _dt_to_str(bundle.snapshot.timestamp),
                    bundle.snapshot.ip,
                    bundle.snapshot.hostname,
                    bundle.snapshot.os,
                    bundle.snapshot.model,
                    bundle.snapshot.device_type.value,
                    bundle.snapshot.confidence
                ))
                result = SaveResult(
                    devices_created=result.devices_created,
                    devices_updated=result.devices_updated,
                    snapshots_saved=1,
                    observations_saved=result.observations_saved,
                    evidence_saved=result.evidence_saved,
                    capabilities_saved=result.capabilities_saved,
                    sessions_updated=result.sessions_updated,
                    elapsed_ms=result.elapsed_ms,
                    success=result.success,
                    error_message=result.error_message,
                )

            # 4. Observations
            for obs in bundle.observations:
                cursor.execute("""
                    INSERT INTO observation 
                    (id, snapshot_id, source, key, value, obs_type, unit, confidence)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    obs.id, obs.snapshot_id, obs.source.value, obs.key, obs.value,
                    obs.obs_type.value, obs.unit, obs.confidence
                ))
            obs_count = len(bundle.observations)

            # 5. Evidence
            for ev in bundle.evidence:
                cursor.execute("""
                    INSERT INTO evidence 
                    (id, snapshot_id, description, contribution, source, details)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    ev.id, ev.snapshot_id, ev.description, ev.contribution,
                    ev.source.value, ev.details
                ))
            ev_count = len(bundle.evidence)

            # 6. Capabilities
            for cap in bundle.capabilities:
                cursor.execute("""
                    INSERT INTO capability 
                    (id, snapshot_id, capability, confidence)
                    VALUES (?, ?, ?, ?)
                """, (
                    cap.id, cap.snapshot_id, cap.capability.value, cap.confidence
                ))
            cap_count = len(bundle.capabilities)

            # 7. CollectorLog
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
            
            # Финальный SaveResult с полной статистикой
            elapsed_ms = (time.time() - start_time) * 1000
            return SaveResult(
                devices_created=result.devices_created,
                devices_updated=result.devices_updated,
                snapshots_saved=result.snapshots_saved,
                observations_saved=obs_count,
                evidence_saved=ev_count,
                capabilities_saved=cap_count,
                sessions_updated=0,  # Пока не используем
                elapsed_ms=elapsed_ms,
                success=True,
                error_message="",
            )

        except Exception as e:
            conn.rollback()
            elapsed_ms = (time.time() - start_time) * 1000
            return SaveResult(
                success=False,
                error_message=str(e),
                elapsed_ms=elapsed_ms,
            )

    def load_latest_snapshots(self, scan_id: str) -> List[Snapshot]:
        """
        Загружает все snapshots для конкретного scan_id.
        Это основа для будущего Report, который будет читать из БД.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, scan_id, device_id, timestamp, ip, hostname, os, model, device_type, confidence
            FROM snapshot
            WHERE scan_id = ?
            ORDER BY ip
        """, (scan_id,))
        
        snapshots = []
        for row in cursor.fetchall():
            snapshots.append(Snapshot(
                id=row[0],
                scan_id=row[1],
                device_id=row[2],
                timestamp=datetime.fromisoformat(row[3]),
                ip=row[4],
                hostname=row[5] or "",
                os=row[6] or "",
                model=row[7] or "",
                device_type=row[8],  # Строка из БД
                confidence=row[9] or 0,
                    def get_last_snapshot(self, device_id: str) -> dict | None:
        """
        Возвращает последний Snapshot устройства (до текущего).
        Используется Event Engine для сравнения состояний.
        
        Возвращает dict или None, если устройства нет в БД.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, scan_id, device_id, timestamp, ip, hostname, os, model, device_type, confidence
            FROM snapshot
            WHERE device_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (device_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "scan_id": row[1],
            "device_id": row[2],
            "timestamp": row[3],
            "ip": row[4],
            "hostname": row[5] or "",
            "os": row[6] or "",
            "model": row[7] or "",
            "device_type": row[8] or "UNKNOWN",
            "confidence": row[9] or 0,
            "vendor": "",  # Vendor хранится в Identity, пока возвращаем пусто
        }
            ))
        return snapshots
