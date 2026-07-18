#!/usr/bin/env python3
"""ConfigRepository - чистое хранилище данных конфигурации."""
from typing import Dict, Any

class ConfigRepository:
    """
    Отвечает только за хранение значений.
    В текущей реализации - in-memory dict.
    В будущем может быть расширен до JSON/YAML/SQLite/Redis без изменения Manager.
    """
    
    def __init__(self):
        self._data: Dict[str, Any] = {}
    
    def set(self, param_id: str, value: Any):
        self._data[param_id] = value
        
    def get(self, param_id: str, default: Any = None) -> Any:
        return self._data.get(param_id, default)
        
    def get_all(self) -> Dict[str, Any]:
        return self._data.copy()
        
    def clear(self):
        self._data.clear()
