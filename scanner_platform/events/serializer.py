#!/usr/bin/env python3
"""Event Serializer - улучшенная сериализация событий."""
import json
from typing import Any
from datetime import datetime
from types import MappingProxyType

class EventSerializer:
    """Улучшенный сериализатор для DomainEventSet."""
    
    @staticmethod
    def serialize(event_set: Any, format: str = "json") -> str:
        """Сериализует DomainEventSet в указанный формат."""
        if format == "json":
            return EventSerializer._to_json(event_set)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    @staticmethod
    def _to_json(event_set: Any) -> str:
        """Конвертирует в JSON без использования asdict()."""
        def convert(obj: Any) -> Any:
            """Рекурсивное преобразование объектов."""
            # datetime
            if isinstance(obj, datetime):
                return obj.isoformat()
            
            # MappingProxyType
            if isinstance(obj, MappingProxyType):
                return {k: convert(v) for k, v in obj.items()}
            
            # Обычный dict
            if isinstance(obj, dict):
                return {k: convert(v) for k, v in obj.items()}
            
            # list/tuple
            if isinstance(obj, (list, tuple)):
                return [convert(item) for item in obj]
            
            # Enum
            if hasattr(obj, 'value') and hasattr(obj, 'name'):
                return obj.value
            
            # Dataclass (проверяем наличие __dataclass_fields__)
            if hasattr(obj, '__dataclass_fields__'):
                result = {}
                for field_name in obj.__dataclass_fields__:
                    field_value = getattr(obj, field_name)
                    result[field_name] = convert(field_value)
                return result
            
            # Примитивы (str, int, float, bool, None)
            return obj
        
        data = {
            "events": [convert(event) for event in event_set.events],
            "generated_at": convert(event_set.generated_at),
            "count": event_set.count()
        }
        
        return json.dumps(data, indent=2)
