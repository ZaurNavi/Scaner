from __future__ import annotations
import time
from typing import List

from .event import Event
from .repository import EventRepository


class EventPersister:
    """
    Event Persister — слой сохранения событий.
    
    Получает List[Event] от Event Engine и сохраняет их в БД.
    Не вычисляет события, не знает про Event Engine.
    Только отвечает на вопрос: "Как сохранить эти события?"
    """

    def __init__(self, repository: EventRepository):
        self.repo = repository

    def persist(self, events: List[Event]) -> PersistResult:
        """
        Сохраняет список событий в БД.
        Возвращает PersistResult с метаданными о сохранении.
        """
        if not events:
            return PersistResult(saved=0, elapsed_ms=0.0, success=True)

        start_time = time.time()
        try:
            saved_count = self.repo.save_events(events)
            elapsed_ms = (time.time() - start_time) * 1000
            return PersistResult(
                saved=saved_count,
                elapsed_ms=elapsed_ms,
                success=True,
            )
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            return PersistResult(
                saved=0,
                elapsed_ms=elapsed_ms,
                success=False,
                error_message=str(e),
            )


from dataclasses import dataclass


@dataclass(frozen=True)
class PersistResult:
    """Результат сохранения событий."""
    saved: int = 0
    elapsed_ms: float = 0.0
    success: bool = True
    error_message: str = ""
