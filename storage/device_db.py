#!/usr/bin/env python3
"""
Repeater Monitor
storage/device_db.py

SQLite-база для долговременной истории устройств.
Хранит MAC, вендора, OS, модель, тип, уверенность,
даты первого/последнего появления, счётчик запусков,
последний IP, последний успешный vendor и пользовательские алиасы/заметки.

v1.6.9.9: Интеграция с Configuration Layer.
Все настройки получаются через ConfigurationManager.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

# v1.6.9.9: Configuration Layer Integration
from configuration import ConfigurationManager, get_config_manager
from models import Device

# Глобальные переменные (инициализируются через initialize())
_db_path: Path | None = None


def initialize(configuration: Optional[ConfigurationManager] = None) -> None:
    """
    Инициализирует Device DB с настройками из Configuration Layer.
    
    v1.6.9.9: Должна быть вызвана один раз при старте приложения.
    
    Args:
        configuration: ConfigurationManager (если None — используется глобальный)
    """
    global _db_path
    
    if configuration is None:
        configuration = get_config_manager()
    
    # Получаем настройки из Configuration Layer
    cache_dir = Path(configuration.get("storage.cache_dir", "cache"))
    _db_path = cache_dir / "devices.db"


def _connect() -> sqlite3.Connection:
    """
    Открывает соединение с БД. Создаёт таблицы, если их нет.
    Выполняет миграции для добавления новых колонок.
    """
    global _db_path
    
    # v1.6.9.9: Если не инициализирован — используем дефолты
    if _db_path is None:
        initialize()

    _db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(_db_path))
    conn.row_factory = sqlite3.Row

    conn.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            mac TEXT PRIMARY KEY,
            last_ip TEXT DEFAULT "",
            vendor TEXT DEFAULT "",
            last_vendor TEXT DEFAULT "",
            hostname TEXT DEFAULT "",
            model TEXT DEFAULT "",
            os TEXT DEFAULT "",
            device_type TEXT DEFAULT "",
            confidence INTEGER DEFAULT 0,
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            seen_count INTEGER DEFAULT 1,
            alias TEXT DEFAULT "",
            notes TEXT DEFAULT ""
        )
    """)

    # Миграции: добавляем колонки, если их нет (для существующих БД)
    existing_columns = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(devices)").fetchall()
    }

    migrations = [
        ("last_ip", 'ALTER TABLE devices ADD COLUMN last_ip TEXT DEFAULT ""'),
        ("last_vendor", 'ALTER TABLE devices ADD COLUMN last_vendor TEXT DEFAULT ""'),
        ("seen_count", 'ALTER TABLE devices ADD COLUMN seen_count INTEGER DEFAULT 1'),
        ("alias", 'ALTER TABLE devices ADD COLUMN alias TEXT DEFAULT ""'),
        ("notes", 'ALTER TABLE devices ADD COLUMN notes TEXT DEFAULT ""'),
    ]

    for column_name, alter_sql in migrations:
        if column_name not in existing_columns:
            conn.execute(alter_sql)

    conn.commit()

    return conn


def load_history() -> dict[str, dict]:
    """
    Возвращает {mac: {данные}} для всех известных устройств.
    """
    if _db_path is None:
        initialize()

    if not _db_path.exists():
        return {}

    with _connect() as conn:
        rows = conn.execute("SELECT * FROM devices").fetchall()

    return {row["mac"]: dict(row) for row in rows}


def save_state(devices: list[Device]) -> None:
    """
    Обновляет last_seen, last_ip, seen_count и сохраняет актуальные данные.
    Сохраняет last_vendor только если vendor != "Unknown".
    НЕ затирает alias и notes (они задаются пользователем вручную).
    """
    if _db_path is None:
        initialize()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with _connect() as conn:
        for d in devices:
            if not d.mac or d.mac == "00:00:00:00:00:00":
                continue

            conn.execute("""
                INSERT INTO devices (
                    mac, last_ip, vendor, last_vendor, hostname, model, os, device_type,
                    confidence, first_seen, last_seen, seen_count, alias, notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, '', '')
                ON CONFLICT(mac) DO UPDATE SET
                    last_ip = excluded.last_ip,
                    vendor = CASE WHEN excluded.vendor != '' AND excluded.vendor != 'Unknown'
                             THEN excluded.vendor ELSE vendor END,
                    last_vendor = CASE WHEN excluded.vendor != '' AND excluded.vendor != 'Unknown'
                                  THEN excluded.vendor ELSE last_vendor END,
                    hostname = CASE WHEN excluded.hostname != ''
                             THEN excluded.hostname ELSE hostname END,
                    model = CASE WHEN excluded.model != ''
                             THEN excluded.model ELSE model END,
                    os = CASE WHEN excluded.os != ''
                             THEN excluded.os ELSE os END,
                    device_type = CASE WHEN excluded.device_type != ''
                             THEN excluded.device_type ELSE device_type END,
                    confidence = excluded.confidence,
                    last_seen = excluded.last_seen,
                    seen_count = seen_count + 1
            """, (
                d.mac, d.ip, d.vendor, d.vendor if d.vendor != "Unknown" else "",
                d.hostname, d.model, d.os, d.device_type,
                d.confidence, now, now
            ))


def get_alias(mac: str) -> str:
    """
    Возвращает пользовательский alias, если задан.
    """
    if _db_path is None:
        initialize()

    if not _db_path.exists():
        return ""

    with _connect() as conn:
        row = conn.execute("SELECT alias FROM devices WHERE mac = ?", (mac,)).fetchone()
        return row["alias"] if row else ""


def set_alias(mac: str, alias: str) -> None:
    """
    Устанавливает пользовательский alias.
    """
    if _db_path is None:
        initialize()

    if not _db_path.exists():
        return

    with _connect() as conn:
        conn.execute("UPDATE devices SET alias = ? WHERE mac = ?", (alias, mac))


def get_notes(mac: str) -> str:
    """
    Возвращает пользовательские заметки, если заданы.
    """
    if _db_path is None:
        initialize()

    if not _db_path.exists():
        return ""

    with _connect() as conn:
        row = conn.execute("SELECT notes FROM devices WHERE mac = ?", (mac,)).fetchone()
        return row["notes"] if row else ""


def set_notes(mac: str, notes: str) -> None:
    """
    Устанавливает пользовательские заметки.
    """
    if _db_path is None:
        initialize()

    if not _db_path.exists():
        return

    with _connect() as conn:
        conn.execute("UPDATE devices SET notes = ? WHERE mac = ?", (notes, mac))
