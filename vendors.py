#!/usr/bin/env python3
"""
Repeater Monitor
vendors.py

Определение производителя устройства по MAC-адресу.
Использует IEEE OUI базу.
"""

from __future__ import annotations

from pathlib import Path

from config import Paths


#
# Кэш базы производителей
#

_VENDOR_CACHE: dict[str, str] | None = None

#
# Кэш найденных производителей
#

_LOOKUP_CACHE: dict[str, str] = {}

DATABASE = Paths.BASE_DIR / "vendors" / "oui.txt"


def load_database() -> dict[str, str]:
    """
    Загружает IEEE OUI базу в память один раз.
    """

    global _VENDOR_CACHE

    if _VENDOR_CACHE is not None:
        return _VENDOR_CACHE

    db = {}

    if not DATABASE.exists():
        raise FileNotFoundError(
            f"Не найден файл базы производителей:\n{DATABASE}"
        )

    with DATABASE.open(
        "r",
        encoding="utf-8",
        errors="ignore",
    ) as file:

        for line in file:

            line = line.strip()

            if not line:
                continue

            if line.startswith("#"):
                continue

            parts = line.split(None, 1)

            if len(parts) != 2:
                continue

            prefix = (
                parts[0]
                .upper()
                .replace("-", "")
                .replace(":", "")
            )

            vendor = parts[1].strip()

            db[prefix] = vendor

    #
    # Пользовательские OUI
    #

    custom = DATABASE.parent / "custom.txt"

    if custom.exists():

        with custom.open(
            "r",
            encoding="utf-8",
            errors="ignore",
        ) as file:

            for line in file:

                line = line.strip()

                if not line:
                    continue

                if line.startswith("#"):
                    continue

                parts = line.split(None, 1)

                if len(parts) != 2:
                    continue

                prefix = (
                    parts[0]
                    .upper()
                    .replace("-", "")
                    .replace(":", "")
                )

                db[prefix] = parts[1].strip()

    _VENDOR_CACHE = db

    return db


def normalize_mac(mac: str) -> str:

    return (
        mac.upper()
        .replace(":", "")
        .replace("-", "")
        .replace(".", "")
    )


def get_vendor(mac: str) -> str:
    """
    Возвращает производителя устройства.
    """

    if not mac:
        return "Unknown"

    mac = normalize_mac(mac)

    if len(mac) < 6:
        return "Unknown"

    #
    # Кэш поиска
    #

    if mac in _LOOKUP_CACHE:
        return _LOOKUP_CACHE[mac]

    db = load_database()

    #
    # IEEE:
    #
    # OUI36
    # OUI28
    # OUI24
    #

    for length in (9, 7, 6):

        prefix = mac[:length]

        vendor = db.get(prefix)

        if vendor:

            _LOOKUP_CACHE[mac] = vendor

            return vendor

    _LOOKUP_CACHE[mac] = "Unknown"

    return "Unknown"
