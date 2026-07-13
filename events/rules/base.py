from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List

from events.models import Event


class BaseRule(ABC):
    """Базовый класс для всех правил детектирования событий."""

    @abstractmethod
    def detect(self, previous_snapshot: dict | None, current_snapshot: dict) -> List[Event]:
        """
        Сравнивает предыдущий и текущий Snapshot.
        Возвращает список событий (может быть пустым).
        """
        pass
