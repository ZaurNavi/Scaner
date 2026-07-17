#!/usr/bin/env python3
"""Event Serializer - сериализация событий."""
import json
from typing import Any
from datetime import datetime
from types import MappingProxyType

class EventSerializer:
    """Сериализатор для DomainEventSet."""
    
    @staticmethod
    def serialize(event_set: Any, format: str = "json") -> str:
        """Сериализует DomainEventSet в указанный формат."""
        if format == "json":
            return EventSerializer._to_json(event_set)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    @staticmethod
    def _to_json(event_set: Any) -> str:
        """Конвертирует в JSON."""
        def custom_encoder(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, MappingProxyType):
                return dict(obj)
            if hasattr(obj, '__dataclass_fields__'):
                return {k: custom_encoder(v) for k, v in obj.__dict__.items()}
            return obj
        
        data = {
            "events": [custom_encoder(event) for event in event_set.events],
            "generated_at": custom_encoder(event_set.generated_at),
            "count": event_set.count()
        }
        
        return json.dumps(data, indent=2)
