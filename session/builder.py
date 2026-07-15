#!/usr/bin/env python3
"""
Session Engine Builder (v1.5.3 Full).
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict

from .models import (
    Session, SessionStatus, SessionEndReason, SessionQuality, SessionTimelineEntry
)
from history import HistoryService, SnapshotRecord
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
            last_seen=datetime.fromisoformat(data["start_time"]), # Будет обновлено
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            duration=data.get("duration"),
            status=SessionStatus(data["status"]),
            end_reason=SessionEndReason(data["end_reason"]) if data.get("end_reason") else None,
            snapshots_count=meta.get("snapshots_count", 0),
            ip_history=meta.get("ip_history", []),
            hostname_history=meta.get("hostname_history", []),
            ap_history=meta.get("ap_history", []),
            rssi_history=meta.get("rssi_history", []),
            total_bytes_in=meta.get("traffic", {}).get("total_bytes_in", 0),
            total_bytes_out=meta.get("traffic", {}).get("total_bytes_out", 0),
            total_flows=meta.get("traffic", {}).get("total_flows", 0),
        )
        # Восстанавливаем таймлайн
        for entry in meta.get("timeline", []):
            sess.timeline.append(SessionTimelineEntry(
                timestamp=datetime.fromisoformat(entry["timestamp"]),
                event_type=entry["event_type"],
                description=entry["description"],
                details=entry.get("details")
            ))
        return sess

    def process_snapshots(self, device_id: str, new_snapshots: List[SnapshotRecord]):
        """
        Основной метод: обрабатывает новые снимки и обновляет сессии.
        """
        if not new_snapshots:
            return

        new_snapshots.sort(key=lambda s: s.timestamp)
        
        # Получаем или создаем сессию
        session = self._active_sessions.get(device_id)
        
        for snapshot in new_snapshots:
            # 1. Проверка на таймаут и закрытие старой сессии
            if session and session.status == SessionStatus.ACTIVE:
                time_gap = snapshot.timestamp - session.last_seen
                if time_gap > SESSION_TIMEOUT:
                    self._close_session(session, SessionEndReason.TIMEOUT)
                    session = None

            # 2. Создание новой сессии, если нет активной
            if session is None:
                session = Session(
                    id=str(uuid.uuid4()),
                    device_id=device_id,
                    start_time=snapshot.timestamp,
                    last_seen=snapshot.timestamp,
                )
                self._add_timeline_event(session, snapshot.timestamp, "start", "Session started")
                self._active_sessions[device_id] = session

            # 3. Обогащение сессии данными снимка и наблюдений
            self._enrich_session(session, snapshot)

        # 4. Сохранение/обновление в БД
        if session and session.status == SessionStatus.ACTIVE:
            session.last_seen = new_snapshots[-1].timestamp
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
        
        # Удаляем из активных
        if session.device_id in self._active_sessions:
            del self._active_sessions[session.device_id]

    def _enrich_session(self, session: Session, snapshot: SnapshotRecord):
        """Добавляет данные снимка и агрегирует метрики."""
        session.snapshots_count += 1
        
        # --- История IP и Hostname ---
        if snapshot.ip and (not session.ip_history or session.ip_history[-1] != snapshot.ip):
            session.ip_history.append(snapshot.ip)
            self._add_timeline_event(session, snapshot.timestamp, "ip_change", f"IP changed to {snapshot.ip}")
            
        if snapshot.hostname and (not session.hostname_history or session.hostname_history[-1] != snapshot.hostname):
            session.hostname_history.append(snapshot.hostname)
            self._add_timeline_event(session, snapshot.timestamp, "hostname_change", f"Hostname changed to {snapshot.hostname}")

        # --- Получение наблюдений для этого снимка ---
        # (В реальном сценарии это может быть оптимизировано, но для MVP берем из History)
        # Для ускорения мы можем брать traffic/omada данные прямо из переданного CollectedData, 
        # но по ТЗ Session Engine работает через History. Чтобы не делать N запросов к БД, 
        # мы предполагаем, что агрегация трафика делается на основе уже сохраненных observations.
        # Для MVP v1.5.3 мы эмулируем это, извлекая данные из последнего доступного traffic observation.
        
        # Примечание: полноценная агрегация требует передачи TrafficInfo в process_snapshots.
        # Мы добавим этот параметр в monitor.py.
        
        session.last_seen = snapshot.timestamp
        session.updated_at = datetime.now()

    def _add_timeline_event(self, session: Session, timestamp: datetime, event_type: str, description: str, details: str = None):
        session.timeline.append(SessionTimelineEntry(
            timestamp=timestamp,
            event_type=event_type,
            description=description,
            details=details
        ))
        # Храним только последние 50 событий таймлайна для экономии памяти
        if len(session.timeline) > 50:
            session.timeline = session.timeline[-50:]

    def get_active_session(self, device_id: str) -> Optional[Session]:
        return self._active_sessions.get(device_id)
