"""
Repeater Monitor
models.py

Структуры данных проекта.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Device:
    """
    Информация об одном устройстве.
    """

    # -----------------------
    # SNMP
    # -----------------------

    ip: str
    mac: str

    # -----------------------
    # Vendor
    # -----------------------

    vendor: str = "Unknown"

    # -----------------------
    # Fingerprint
    # -----------------------

    hostname: str = ""
    model: str = ""
    os: str = ""
    device_type: str = ""
    confidence: int = 0

    # -----------------------
    # NetFlow
    # -----------------------

    flows: int = 0

    bytes: int = 0

    megabytes: float = 0.0

    first_seen: str = ""

    duration_seconds: float = 0.0

    hours_online: float = 0.0

    mb_per_hour: float = 0.0

    # -----------------------
    # Detection
    # -----------------------

    status: str = ""

    reason: str = ""
