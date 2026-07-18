#!/usr/bin/env python3
"""ConfigValidator - строгая проверка типов и значений."""
import ipaddress
from pathlib import Path
from datetime import timedelta
from typing import Any, Type
from .models import ConfigValue
from .exceptions import ConfigValidationError

class ConfigValidator:
    """Валидатор конфигурации."""
    
    @staticmethod
    def validate(param: ConfigValue, value: Any) -> Any:
        """
        Проверяет и при необходимости преобразует значение.
        Возвращает валидное значение нужного типа.
        """
        if value is None:
            if param.default is None:
                raise ConfigValidationError(f"Parameter {param.id} is required but missing")
            return param.default
        
        parsed_value = ConfigValidator._parse_type(param.type, value)
        
        if param.validator is not None:
            if not param.validator(parsed_value):
                raise ConfigValidationError(f"Parameter {param.id} failed custom validation: {value}")
        
        return parsed_value
    
    @staticmethod
    def _parse_type(target_type: Type, value: Any) -> Any:
        """Преобразует значение к целевому типу."""
        if isinstance(value, target_type):
            return value
            
        if target_type is bool:
            if isinstance(value, str):
                return value.lower() in ('true', '1', 'yes', 'on')
            return bool(value)
            
        if target_type is int:
            return int(value)
            
        if target_type is float:
            return float(value)
            
        if target_type is str:
            return str(value)
            
        if target_type is Path:
            return Path(value)
            
        if target_type is timedelta:
            if isinstance(value, (int, float)):
                return timedelta(seconds=value)
            return value # Assume it's already timedelta
            
        if target_type is ipaddress.IPv4Network:
            if isinstance(value, str):
                return ipaddress.IPv4Network(value, strict=False)
            return value
            
        # Fallback for Enums or other types
        if hasattr(target_type, '_member_names_'): # Enum check
            return target_type(value)
            
        return value
