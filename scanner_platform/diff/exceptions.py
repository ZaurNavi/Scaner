#!/usr/bin/env python3
"""Исключения для Change Detection Layer."""

class DifferentIdentityError(Exception):
    """Вызывается при попытке сравнить профили разных устройств."""
    pass

class InvalidProfileError(Exception):
    """Вызывается при передаче некорректного или неполного профиля."""
    pass
