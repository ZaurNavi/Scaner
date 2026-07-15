#!/usr/bin/env python3
"""
Core Session Builder (MVP).
Группирует Snapshot'ы в сессии по правилу SESSION_TIMEOUT.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import List, Dict

from .models import Session, SessionStatus, SessionEndReason
from history import HistoryService, SnapshotRecord


# Настройка из ТЗ
SESSION_TIMEOUT = timedelta(minutes=20)


class SessionBuilder:
    """
    Строит сессии из истории Snapshot'ов.
    Работает только через HistoryService, без прямого доступа к БД.
    """
    
    def __init__(self, history_service: HistoryService):
        self.history_service = history_service

    def build_sessions(self, device_id: str) -> List[Session]:
        """
        Строит список сессий для устройства.
        
        Args:
            device_id: Идентификатор устройства из Archivist.
            
        Returns:
            Список сессий, отсортированный по времени (новые последними).
        """
        # Получаем все snapshot'ы устройства через HistoryService
        snapshots = self.history_service.get_snapshots(device_id)
        if not snapshots:
            return []

        # Сортируем по времени на всякий случай
        snapshots.sort(key=lambda s: s.timestamp)
        
        sessions: List[Session] = []
        current_session: Optional[Session] = None
        
        for snapshot in snapshots:
            # Если текущей сессии нет, создаем новую
            if current_session is None:
                current_session = Session(
                    id=self._generate_session_id(device_id, snapshot.timestamp),
                    device_id=device_id,
                    start_time=snapshot.timestamp
                )
            
            # Проверяем, нужно ли закрыть текущую сессию
            if self._should_close_session(current_session, snapshot.timestamp):
                self._finalize_session(current_session, snapshot.timestamp, SessionEndReason.TIMEOUT)
                sessions.append(current_session)
                # Создаем новую сессию
                current_session = Session(
                    id=self._generate_session_id(device_id, snapshot.timestamp),
                    device_id=device_id,
                    start_time=snapshot.timestamp
                )
            
            # Добавляем данные в текущую сессию
            self._add_to_session(current_session, snapshot)
        
        # Завершаем последнюю сессию, если она активна
        if current_session and current_session.status == SessionStatus.ACTIVE:
            # Для активной сессии end_time = last_seen
            last_seen = self.history_service.get_last_seen(device_id)
            if last_seen:
                self._finalize_session(current_session, last_seen, SessionEndReason.UNKNOWN)
            sessions.append(current_session)
        
        return sessions

    def _should_close_session(self, session: Session, current_timestamp: datetime) -> bool:
        """Проверяет, нужно ли закрыть сессию из-за таймаута."""
        if session.end_time is not None:
            return False
        return current_timestamp - session.start_time > SESSION_TIMEOUT

    def _finalize_session(self, session: Session, end_time: datetime, reason: SessionEndReason):
        """Завершает сессию и делает ее неизменяемой."""
        session.end_time = end_time
        session.duration = (end_time - session.start_time).total_seconds()
        session.status = SessionStatus.ENDED
        session.end_reason = reason
        session.updated_at = datetime.now()

    def _add_to_session(self, session: Session, snapshot: SnapshotRecord):
        """Добавляет данные из snapshot в сессию."""
        if snapshot.ip and snapshot.ip not in session.ip_history:
            session.ip_history.append(snapshot.ip)
        if snapshot.hostname and snapshot.hostname not in session.hostname_history:
            session.hostname_history.append(snapshot.hostname)
        session.updated_at = datetime.now()

    def _generate_session_id(self, device_id: str, timestamp: datetime) -> str:
        """Генерирует уникальный ID для сессии."""
        import uuid
        return str(uuid.uuid4())
