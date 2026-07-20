#!/usr/bin/env python3
"""
Repeater Monitor
vendors.py

Определение производителя устройства по MAC-адресу.
Использует IEEE OUI базу.
v1.7.1a: Интеграция с Configuration Layer.
"""

from __future__ import annotations
from pathlib import Path
from configuration import get_config_manager

_VENDOR_CACHE: dict[str, str] | None = None
_LOOKUP_CACHE: dict[str, str] = {}


def _get_database_path() -> Path:
    """Получает путь к базе данных из Configuration Layer."""
    config = get_config_manager()
    db_path = config.get("fingerprint.vendors.database_path", "vendors/oui.txt")
    return Path(db_path)


def load_database() -> dict[str, str]:
    global _VENDOR_CACHE

    if _VENDOR_CACHE is not None:
        return _VENDOR_CACHE

    db = {}
    database = _get_database_path()

    if not database.exists():
        return db  # Возвращаем пустой dict, чтобы не ломать систему, если файла нет

    with database.open("r", encoding="utf-8", errors="ignore") as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split(None, 1)
            if len(parts) != 2:
                continue

            prefix = parts[0].upper().replace("-", "").replace(":", "")
            db[prefix] = parts[1].strip()

    # Пользовательские OUI
    custom = database.parent / "custom.txt"
    if custom.exists():
        with custom.open("r", encoding="utf-8", errors="ignore") as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                parts = line.split(None, 1)
                if len(parts) != 2:
                    continue

                prefix = parts[0].upper().replace("-", "").replace(":", "")
                db[prefix] = parts[1].strip()

    _VENDOR_CACHE = db
    return db


def normalize_mac(mac: str) -> str:
    return mac.upper().replace(":", "").replace("-", "").replace(".", "")


def get_vendor(mac: str) -> str:
    if not mac or len(normalize_mac(mac)) < 6:
        return "Unknown"

    mac_norm = normalize_mac(mac)

    if mac_norm in _LOOKUP_CACHE:
        return _LOOKUP_CACHE[mac_norm]

    db = load_database()

    for length in (9, 7, 6):
        prefix = mac_norm[:length]
        vendor = db.get(prefix)
        if vendor:
            _LOOKUP_CACHE[mac_norm] = vendor
            return vendor

    _LOOKUP_CACHE[mac_norm] = "Unknown"
    return "Unknown"
