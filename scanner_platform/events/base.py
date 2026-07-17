#!/usr/bin/env python3
"""Базовые модели для Domain Events."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Tuple
from types import MappingProxyType
from enum import Enum
import hashlib

class EventOrigin(Enum):
    PROFILE = "PROFILE"
    DIFF = "DIFF"
    RULE = "RULE"
    SYSTEM = "SYSTEM"

@dataclass(frozen=True)
class DomainEvent:
    """
    Полностью immutable доменное событие.
    Не содержит severity, risk, alert - это ответственность следующих слоёв.
    """
    event_id: str
    event_type: str
    device_uuid: str
    occurred_at: datetime
    payload: MappingProxyType
    source_diff_id: str
    source_change_id: str
    origin: EventOrigin
    
    @classmethod
    def create(
        cls,
        event_type: str,
        device_uuid: str,
        payload: Dict[str, Any],
        source_diff_id: str,
        source_change_id: str,
        occurred_at: datetime,  # ОБЯЗАТЕЛЬНЫЙ параметр для детерминированности
        origin: EventOrigin = EventOrigin.RULE
    ) -> 'DomainEvent':
        """Фабричный метод с детерминированным event_id."""
        # Детерминированный event_id (без occurred_at)
        id_payload = f"{event_type}|{device_uuid}|{str(payload)}|{source_change_id}"
        event_id = hashlib.sha256(id_payload.encode('utf-8')).hexdigest()[:16]
        
        return cls(
            event_id=event_id,
            event_type=event_type,
            device_uuid=device_uuid,
            occurred_at=occurred_at,
            payload=MappingProxyType(payload),
            source_diff_id=source_diff_id,
            source_change_id=source_change_id,
            origin=origin
        )
