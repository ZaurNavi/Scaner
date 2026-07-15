from __future__ import annotations
import json
import sqlite3
import time
from datetime import datetime
from typing import List, Any
from .database import DatabaseManager
from storage.schema import SnapshotBundle, SaveResult


def _dt_to_str(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


class Repository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def save_bundle(self, bundle: SnapshotBundle) -> SaveResult:
        start_time = time.time()
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("BEGIN IMMEDIATE")

            # 1. Scan
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

            # 2. Device
            actual_device_id = ""
            if bundle.device:
                cursor.execute("SELECT id FROM device WHERE mac = ?", (bundle.device.mac,))
                existing = cursor.fetchone()
                
                if existing:
                    actual_device_id = existing[0]
                    cursor.execute("""
                        UPDATE device SET last_seen = ?, status = ? WHERE id = ?
                    """, (
                        _dt_to_str(bundle.device.last_seen),
                        bundle.device.status.value,
                        actual_device_id
                    ))
                    result = SaveResult(
                        device_id=actual_device_id,
                        devices_updated=1,
                        elapsed_ms=(time.time() - start_time) * 1000,
                        success=True
                    )
                else:
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
                        device_id=actual_device_id,
                        devices_created=1,
                        elapsed_ms=(time.time() - start_time) * 1000,
                        success=True
                    )
            else:
                actual_device_id = bundle.snapshot.device_id if bundle.snapshot else ""
                result = SaveResult(device_id=actual_device_id, elapsed_ms=(time.time() - start_time) * 1000, success=True)

            # 3. Snapshot
            obs_count = 0
            ev_count = 0
            cap_count = 0
            
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
                    device_id=result.device_id,
                    devices_created=result.devices_created,
                    devices_updated=result.devices_updated,
                    snapshots_saved=1,
                    elapsed_ms=result.elapsed_ms,
                    success=True
                )

            # 4. Observations
            for obs in bundle.observations:
                cursor.execute("""
                    INSERT INTO observation (id, snapshot_id, source, key, value, obs_type, unit, confidence)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (obs.id, obs.snapshot_id, obs.source.value, obs.key, obs.value, obs.obs_type.value, obs.unit, obs.confidence))
            obs_count = len(bundle.observations)

            # 5. Evidence
            for ev in bundle.evidence:
                cursor.execute("""
                    INSERT INTO evidence (id, snapshot_id, description, contribution, source, details)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (ev.id, ev.snapshot_id, ev.description, ev.contribution, ev.source.value, ev.details))
            ev_count = len(bundle.evidence)

            # 6. Capabilities
            for cap in bundle.capabilities:
                cursor.execute("""
                    INSERT INTO capability (id, snapshot_id, capability, confidence)
                    VALUES (?, ?, ?, ?)
                """, (cap.id, cap.snapshot_id, cap.capability.value, cap.confidence))
            cap_count = len(bundle.capabilities)

            # 7. CollectorLog
            if bundle.collector_log:
                cursor.execute("""
                    INSERT INTO collector_log (id, scan_id, collector_name, started_at, finished_at, duration_ms, objects_processed, status, warnings, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    bundle.collector_log.id, bundle.collector_log.scan_id, bundle.collector_log.collector_name,
                    _dt_to_str(bundle.collector_log.started_at), _dt_to_str(bundle.collector_log.finished_at),
                    bundle.collector_log.duration_ms, bundle.collector_log.objects_processed,
                    bundle.collector_log.status.value, bundle.collector_log.warnings, bundle.collector_log.error_message
                ))

            conn.commit()
            
            return SaveResult(
                device_id=result.device_id,
                devices_created=result.devices_created,
                devices_updated=result.devices_updated,
                snapshots_saved=result.snapshots_saved,
                observations_saved=obs_count,
                evidence_saved=ev_count,
                capabilities_saved=cap_count,
                sessions_updated=0,
                elapsed_ms=(time.time() - start_time) * 1000,
                success=True,
                error_message="",
            )

        except Exception as e:
            conn.rollback()
            return SaveResult(
                success=False,
                error_message=str(e),
                elapsed_ms=(time.time() - start_time) * 1000,
            )

    def get_last_snapshot(self, device_id: str) -> dict | None:
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
            "vendor": "",
        }

    # === v1.5.3: Session Engine Methods ===
    
    def get_active_sessions(self) -> List[dict]:
        """Возвращает все сессии со статусом ACTIVE для Recovery."""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT id, device_id, start_time, end_time, duration, status, end_reason, metadata
            FROM session
            WHERE status = 'ACTIVE'
        """)
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def create_session(self, session: 'Session'):
        """Создает новую запись сессии в БД."""
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO session (id, device_id, source, start_time, end_time, duration, bytes_in, bytes_out, flows, status, end_reason, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session.id, session.device_id, "session_engine",
            session.start_time.isoformat(),
            session.end_time.isoformat() if session.end_time else None,
            session.duration,
            session.total_bytes_in, session.total_bytes_out, session.total_flows,
            session.status.value,
            session.end_reason.value if session.end_reason else None,
            json.dumps(session.to_dict())
        ))
        self.db.commit()

    def update_session(self, session: 'Session'):
        """Обновляет активную сессию."""
        cursor = self.db.cursor()
        cursor.execute("""
            UPDATE session 
            SET duration = ?, bytes_in = ?, bytes_out = ?, flows = ?, status = ?, metadata = ?, updated_at = ?
            WHERE id = ? AND status = 'ACTIVE'
        """, (
            session.duration,
            session.total_bytes_in, session.total_bytes_out, session.total_flows,
            session.status.value,
            json.dumps(session.to_dict()),
            session.updated_at.isoformat(),
            session.id
        ))
        self.db.commit()

    def close_session(self, session: 'Session'):
        """Неизменяемо закрывает сессию."""
        cursor = self.db.cursor()
        cursor.execute("""
            UPDATE session 
            SET status = ?, end_time = ?, duration = ?, end_reason = ?, metadata = ?, updated_at = ?
            WHERE id = ?
        """, (
            session.status.value,
            session.end_time.isoformat() if session.end_time else None,
            session.duration,
            session.end_reason.value if session.end_reason else None,
            json.dumps(session.to_dict()),
            session.updated_at.isoformat(),
            session.id
        ))
        self.db.commit()
