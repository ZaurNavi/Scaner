#!/usr/bin/env python3
"""ConfigRegistry - приватный реестр всех параметров платформы."""
from typing import Dict, Optional, Any, Callable, Type
from .models import ConfigValue, ConfigGroup
from .exceptions import ConfigUnknownParameterError

class ConfigRegistry:
    """
    Приватный реестр параметров.
    Отвечает за метаданные, но не за значения.
    Доступ только через ConfigurationManager.
    """
    
    def __init__(self):
        self._parameters: Dict[str, ConfigValue] = {}
        self._groups: Dict[str, ConfigGroup] = {}
    
    def register(
        self,
        param_id: str,
        param_type: Type,
        default: Any,
        group: str,
        description: str,
        validator: Optional[Callable[[Any], bool]] = None,
        mutable: bool = False,
        deprecated: bool = False,
        required: bool = False,
        min_value: Optional[Any] = None,
        max_value: Optional[Any] = None
    ):
        """Регистрирует новый параметр."""
        if param_id in self._parameters:
            raise ValueError(f"Parameter {param_id} already registered")
        
        self._parameters[param_id] = ConfigValue(
            id=param_id,
            name=param_id.split('.')[-1],
            group=group,
            type=param_type,
            default=default,
            description=description,
            validator=validator,
            mutable=mutable,
            deprecated=deprecated,
            required=required,
            min_value=min_value,
            max_value=max_value
        )
        
        if group not in self._groups:
            self._groups[group] = ConfigGroup(name=group, description=f"{group} settings")
        self._groups[group].parameters.append(param_id)
    
    def get(self, param_id: str) -> ConfigValue:
        """Получает метаданные параметра."""
        if param_id not in self._parameters:
            raise ConfigUnknownParameterError(f"Unknown parameter: {param_id}")
        return self._parameters[param_id]
    
    def get_all(self) -> Dict[str, ConfigValue]:
        """Получает все зарегистрированные параметры."""
        return self._parameters.copy()
    
    def get_group(self, group_name: str) -> Dict[str, ConfigValue]:
        """Получает параметры конкретной группы."""
        return {
            pid: p for pid, p in self._parameters.items() if p.group == group_name
        }
    
    def clear(self):
        """Очищает реестр (используется в тестах)."""
        self._parameters.clear()
        self._groups.clear()
