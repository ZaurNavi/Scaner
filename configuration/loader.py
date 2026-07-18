#!/usr/bin/env python3
"""ConfigLoader - загрузка конфигурации из различных источников."""
import json
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigLoader:
    """Загрузчик конфигурации из JSON/YAML/env."""
    
    @staticmethod
    def from_json(file_path: str) -> Dict[str, Any]:
        """Загружает конфигурацию из JSON файла."""
        path = Path(file_path)
        if not path.exists():
            return {}
        
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> Dict[str, Any]:
        """Загружает конфигурацию из словаря."""
        return data.copy()
    
    @staticmethod
    def from_env(prefix: str = "SCANNER_") -> Dict[str, Any]:
        """Загружает конфигурацию из переменных окружения."""
        import os
        config = {}
        for key, value in os.environ.items():
            if key.startswith(prefix):
                param_id = key[len(prefix):].lower().replace('_', '.')
                config[param_id] = value
        return config
    
    @staticmethod
    def merge(*sources: Dict[str, Any]) -> Dict[str, Any]:
        """Объединяет несколько источников конфигурации (последний приоритетнее)."""
        result = {}
        for source in sources:
            result.update(source)
        return result
