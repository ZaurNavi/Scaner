#!/usr/bin/env python3
"""
Repeater Monitor
storage/history.py

Бизнес-логика обогащения устройств историческими данными.
"""

from __future__ import annotations

from models import Device

from .device_db import load_history


def enrich(devices: list[Device]) -> list[Device]:
    """
    Применяет историю из БД к списку устройств.
    Заполняет пустые поля историческими данными,
    не затирая свежие значения.
    """

    history = load_history()

    for d in devices:
        if d.mac not in history:
            continue

        h = history[d.mac]

        # Vendor: если сейчас Unknown, берём из истории
        if d.vendor == "Unknown":
            # Сначала пробуем last_vendor (последнее успешное определение)
            if h.get("last_vendor"):
                d.vendor = h["last_vendor"]
            elif h.get("vendor") and h["vendor"] != "Unknown":
                d.vendor = h["vendor"]

        if not d.hostname:
            d.hostname = h.get("hostname", "")

        if not d.model:
            d.model = h.get("model", "")

        if not d.os:
            d.os = h.get("os", "")

        if not d.device_type:
            d.device_type = h.get("device_type", "")

    return devices
