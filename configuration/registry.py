#!/usr/bin/env python3
"""ConfigRegistry - реестр всех параметров платформы."""
from typing import Dict, Optional, Any, Callable, Type
from .models import ConfigValue, ConfigGroup
from .exceptions import ConfigUnknownParameterError

class ConfigRegistry:
    """Реестр параметров. Отвечает за метаданные, но не за значения."""
    
    _parameters: Dict[str, ConfigValue] = {}
    _groups: Dict[str, ConfigGroup] = {}
    
    @classmethod
    def register(
        cls,
        param_id: str,
        param_type: Type,
        default: Any,
        group: str,
        description: str,
        validator: Optional[Callable[[Any], bool]] = None,
        mutable: bool = False,
        deprecated: bool = False
    ):
        """Регистрирует новый параметр."""
        if param_id in cls._parameters:
            raise ValueError(f"Parameter {param_id} already registered")
        
        cls._parameters[param_id] = ConfigValue(
            id=param_id,
            name=param_id.split('.')[-1],
            group=group,
            type=param_type,
            default=default,
            description=description,
            validator=validator,
            mutable=mutable,
            deprecated=deprecated
        )
        
        if group not in cls._groups:
            cls._groups[group] = ConfigGroup(name=group, description=f"{group} settings")
        cls._groups[group].parameters.append(param_id)
    
    @classmethod
    def get(cls, param_id: str) -> ConfigValue:
        """Получает метаданные параметра."""
        if param_id not in cls._parameters:
            raise ConfigUnknownParameterError(f"Unknown parameter: {param_id}")
        return cls._parameters[param_id]
    
    @classmethod
    def get_all(cls) -> Dict[str, ConfigValue]:
        """Получает все зарегистрированные параметры."""
        return cls._parameters.copy()
    
    @classmethod
    def get_group(cls, group_name: str) -> Dict[str, ConfigValue]:
        """Получает параметры конкретной группы."""
        return {
            pid: p for pid, p in cls._parameters.items() if p.group == group_name
        }
    
    @classmethod
    def clear(cls):
        """Очищает реестр (используется в тестах)."""
        cls._parameters.clear()
        cls._groups.clear()
