#!/usr/bin/env python3
"""
Core Session Builder (MVP).
Группирует Snapshot'ы в сессии по правилу SESSION_TIMEOUT.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import List, Optional

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

        # Сортируем по времени
        snapshots.sort(key=lambda s: s.timestamp)
        
        sessions: List[Session] = []
        current_session: Optional[Session] = None
        
        for snapshot in snapshots:
            # Если текущей сессии нет, создаем новую
            if current_session is None:
                current_session = Session(
                    id=str(uuid.uuid4()),
                    device_id=device_id,
                    start_time=snapshot.timestamp,
                    last_seen=snapshot.timestamp
                )
                self._add_to_session(current_session, snapshot)
                continue
            
            # Проверяем, нужно ли закрыть текущую сессию из-за разрыва
            time_gap = snapshot.timestamp - current_session.last_seen
            if time_gap > SESSION_TIMEOUT:
                # Закрываем текущую сессию
                self._finalize_session(current_session, SessionEndReason.TIMEOUT)
                sessions.append(current_session)
                # Создаем новую сессию
                current_session = Session(
                    id=str(uuid.uuid4()),
                    device_id=device_id,
                    start_time=snapshot.timestamp,
                    last_seen=snapshot.timestamp
                )
                self._add_to_session(current_session, snapshot)
            else:
                # Продолжаем текущую сессию
                current_session.last_seen = snapshot.timestamp
                self._add_to_session(current_session, snapshot)
        
        # Завершаем последнюю сессию (она остаётся активной, но фиксируем last_seen)
        if current_session:
            # Для MVP: последняя сессия считается ENDED с причиной UNKNOWN
            # В полной версии она будет ACTIVE до следующего запуска
            self._finalize_session(current_session, SessionEndReason.UNKNOWN)
            sessions.append(current_session)
        
        return sessions

    def _finalize_session(self, session: Session, reason: SessionEndReason):
        """Завершает сессию и делает ее неизменяемой."""
        session.end_time = session.last_seen
        session.duration = (session.end_time - session.start_time).total_seconds()
        session.status = SessionStatus.ENDED
        session.end_reason = reason
        session.updated_at = datetime.now()

    def _add_to_session(self, session: Session, snapshot: SnapshotRecord):
        """Добавляет данные из snapshot в сессию."""
        session.snapshots_count += 1
        if snapshot.ip and (not session.ip_history or session.ip_history[-1] != snapshot.ip):
            session.ip_history.append(snapshot.ip)
        if snapshot.hostname and (not session.hostname_history or session.hostname_history[-1] != snapshot.hostname):
            session.hostname_history.append(snapshot.hostname)
        session.updated_at = datetime.now()
