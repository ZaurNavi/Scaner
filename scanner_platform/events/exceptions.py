#!/usr/bin/env python3
"""Исключения для Domain Event Layer."""

class InvalidDiffError(Exception):
    """Вызывается при передаче некорректного ProfileDiff."""
    pass

class EventGenerationError(Exception):
    """Вызывается при ошибке генерации событий."""
    pass
