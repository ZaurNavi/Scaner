#!/usr/bin/env python3
"""ConfigSerializer - сериализация конфигурации."""
import json
from pathlib import Path
from typing import Dict, Any

class ConfigSerializer:
    """Сериализатор конфигурации."""
    
    @staticmethod
    def to_json(config: Dict[str, Any], indent: int = 2) -> str:
        """Сериализует конфигурацию в JSON строку."""
        return json.dumps(config, indent=indent, default=str)
    
    @staticmethod
    def to_file(config: Dict[str, Any], file_path: str, indent: int = 2):
        """Сохраняет конфигурацию в JSON файл."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=indent, default=str)
