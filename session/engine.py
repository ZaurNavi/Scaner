#!/usr/bin/env python3
"""
Session Engine (v1.5.3 Full).
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict

from .models import (
    Session, SessionStatus, SessionEndReason, SessionQuality, SessionTimelineEntry
)
from history import HistoryService
from storage.archivist import Repository


SESSION_TIMEOUT = timedelta(minutes=20)


class SessionEngine:
    def __init__(self, history_service: HistoryService, repository: Repository):
        self.history = history_service
        self.repo = repository
        self._active_sessions: Dict[str, Session] = {}
        self._load_active_sessions()

    def _load_active_sessions(self):
        """Recovery: загружает ACTIVE сессии из БД при старте."""
        try:
            active_sessions = self.repo.get_active_sessions()
            for sess_dict in active_sessions:
                sess = self._dict_to_session(sess_dict)
                sess.quality = SessionQuality.RECOVERED
                self._active_sessions[sess.device_id] = sess
        except Exception as e:
            print(f"  [SESSION] ⚠️ Recovery failed: {e}")

    def _dict_to_session(self, data: dict) -> Session:
        """Восстанавливает объект Session из словаря БД."""
        meta = json.loads(data.get("metadata", "{}")) if data.get("metadata") else {}
        
        sess = Session(
            id=data["id"],
            device_id=data["device_id"],
            start_time=datetime.fromisoformat(data["start_time"]),
            last_seen=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            duration=data.get("duration"),
            status=SessionStatus(data.get("status", "ACTIVE")),
            end_reason=SessionEndReason(data["end_reason"]) if data.get("end_reason") else None,
            snapshots_count=meta.get("snapshots_count", 0),
            ip_history=meta.get("ip_history", []),
            hostname_history=meta.get("hostname_history", []),
            total_bytes_in=meta.get("traffic", {}).get("total_bytes_in", 0),
            total_bytes_out=meta.get("traffic", {}).get("total_bytes_out", 0),
            total_flows=meta.get("traffic", {}).get("total_flows", 0),
        )
        
        for entry in meta.get("timeline", []):
            sess.timeline.append(SessionTimelineEntry(
                timestamp=datetime.fromisoformat(entry["timestamp"]),
                event_type=entry["event_type"],
                description=entry["description"],
                details=entry.get("details")
            ))
        return sess

    def process_snapshots(self, device_id: str, new_snapshots: List[dict]):
        """Обрабатывает новые снимки и обновляет сессии."""
        if not new_snapshots:
            return

        new_snapshots.sort(key=lambda s: datetime.fromisoformat(s["timestamp"]))
        
        session = self._active_sessions.get(device_id)
        
        for snap in new_snapshots:
            snap_time = datetime.fromisoformat(snap["timestamp"])
            
            if session and session.status == SessionStatus.ACTIVE:
                time_gap = snap_time - session.last_seen
                if time_gap > SESSION_TIMEOUT:
                    self._close_session(session, SessionEndReason.TIMEOUT)
                    session = None

            if session is None:
                session = Session(
                    id=str(uuid.uuid4()),
                    device_id=device_id,
                    start_time=snap_time,
                    last_seen=snap_time,
                )
                self._add_timeline_event(session, snap_time, "start", "Session started")
                self._active_sessions[device_id] = session
                self.repo.create_session(session)

            self._enrich_session(session, snap)

        if session and session.status == SessionStatus.ACTIVE:
            session.last_seen = datetime.fromisoformat(new_snapshots[-1]["timestamp"])
            session.duration = (session.last_seen - session.start_time).total_seconds()
            session.updated_at = datetime.now()
            self.repo.update_session(session)

    def close_all_active_sessions(self, reason: SessionEndReason = SessionEndReason.PROGRAM_SHUTDOWN):
        """Вызывается при завершении работы программы."""
        for device_id, session in list(self._active_sessions.items()):
            if session.status == SessionStatus.ACTIVE:
                self._close_session(session, reason)

    def _close_session(self, session: Session, reason: SessionEndReason):
        """Неизменяемое закрытие сессии."""
        session.end_time = session.last_seen
        session.duration = (session.end_time - session.start_time).total_seconds()
        session.status = SessionStatus.ENDED
        session.end_reason = reason
        session.quality = SessionQuality.COMPLETE if session.snapshots_count > 1 else SessionQuality.PARTIAL
        session.updated_at = datetime.now()
        
        self._add_timeline_event(session, session.end_time, "end", f"Session ended: {reason.value}")
        self.repo.close_session(session)
        
        if session.device_id in self._active_sessions:
            del self._active_sessions[session.device_id]

    def _enrich_session(self, session: Session, snap: dict):
        """Добавляет данные снимка в сессию."""
        session.snapshots_count += 1
        
        if snap.get("ip") and (not session.ip_history or session.ip_history[-1] != snap["ip"]):
            session.ip_history.append(snap["ip"])
            self._add_timeline_event(session, datetime.fromisoformat(snap["timestamp"]), "ip_change", f"IP changed to {snap['ip']}")
            
        if snap.get("hostname") and (not session.hostname_history or session.hostname_history[-1] != snap["hostname"]):
            session.hostname_history.append(snap["hostname"])
            self._add_timeline_event(session, datetime.fromisoformat(snap["timestamp"]), "hostname_change", f"Hostname changed to {snap['hostname']}")

        session.last_seen = datetime.fromisoformat(snap["timestamp"])
        session.updated_at = datetime.now()

    def _add_timeline_event(self, session: Session, timestamp: datetime, event_type: str, description: str, details: str = None):
        session.timeline.append(SessionTimelineEntry(
            timestamp=timestamp,
            event_type=event_type,
            description=description,
            details=details
        ))
        if len(session.timeline) > 50:
            session.timeline = session.timeline[-50:]

    def get_active_session(self, device_id: str) -> Optional[Session]:
        return self._active_sessions.get(device_id)
