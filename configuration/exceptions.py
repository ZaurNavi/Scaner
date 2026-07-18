#!/usr/bin/env python3
"""Исключения Configuration Layer."""

class ConfigError(Exception):
    """Базовое исключение конфигурации."""
    pass

class ConfigFrozenError(ConfigError):
    """Вызывается при попытке изменить конфигурацию после freeze()."""
    pass

class ConfigValidationError(ConfigError):
    """Вызывается при ошибке валидации типа или значения."""
    pass

class ConfigUnknownParameterError(ConfigError):
    """Вызывается при запросе незарегистрированного параметра."""
    pass

class ConfigMissingParameterError(ConfigError):
    """Вызывается при отсутствии обязательного параметра."""
    pass
