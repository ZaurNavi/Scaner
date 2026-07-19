#!/usr/bin/env python3
"""
Active Cache для результатов коллекторов.
Использует WAL-режим для лучшей параллельной записи.

v1.6.9.9: Интеграция с Configuration Layer.
Все настройки получаются через ConfigurationManager.
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Optional

# v1.6.9.9: Configuration Layer Integration
from configuration import ConfigurationManager, get_config_manager

# Глобальные переменные (инициализируются через initialize())
_connection: sqlite3.Connection | None = None
_cache_enabled: bool = True
_ttl_map: dict[str, int] = {}
_max_retries: int = 3
_cache_dir: Path = Path("cache")
_cache_db: Path | None = None


def initialize(configuration: Optional[ConfigurationManager] = None) -> None:
    """
    Инициализирует Active Cache с настройками из Configuration Layer.
    
    v1.6.9.9: Должна быть вызвана один раз при старте приложения.
    
    Args:
        configuration: ConfigurationManager (если None — используется глобальный)
    """
    global _cache_enabled, _ttl_map, _max_retries, _cache_dir, _cache_db
    
    if configuration is None:
        configuration = get_config_manager()
    
    # Получаем настройки из Configuration Layer
    _cache_enabled = configuration.get("cache.enabled", True)
    _max_retries = configuration.get("cache.max_retries", 3)
    _cache_dir = Path(configuration.get("storage.cache_dir", "cache"))
    _cache_db = _cache_dir / "active_cache.db"
    
    # TTL для каждого коллектора
    _ttl_map = {
        "ttl": configuration.get("cache.ttl.ttl", 300),
        "tcp": configuration.get("cache.ttl.tcp", 600),
        "http": configuration.get("cache.ttl.http", 3600),
        "ssdp": configuration.get("cache.ttl.ssdp", 1800),
        "snmp": configuration.get("cache.ttl.snmp", 900),
    }


def _get_connection() -> sqlite3.Connection:
    """
    Возвращает глобальное соединение с БД.
    Создаёт таблицу и включает WAL-режим при первом вызове.
    """
    global _connection

    if _connection is None:
        # v1.6.9.9: Если не инициализирован — используем дефолты
        if _cache_db is None:
            initialize()
        
        _cache_dir.mkdir(parents=True, exist_ok=True)
        _connection = sqlite3.connect(str(_cache_db), check_same_thread=False)
        _connection.row_factory = sqlite3.Row

        # Включаем WAL-режим для лучшей параллельной записи
        _connection.execute("PRAGMA journal_mode=WAL")
        _connection.execute("PRAGMA synchronous=NORMAL")

        # Создаём таблицу
        _connection.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                ip TEXT,
                collector TEXT,
                timestamp REAL,
                data TEXT,
                PRIMARY KEY (ip, collector)
            )
        """)

        # Автоочистка старых записей
        cutoff = time.time() - max(_ttl_map.values())
        _connection.execute("DELETE FROM cache WHERE timestamp < ?", (cutoff,))
        _connection.commit()

    return _connection


def get(ip: str, collector: str) -> dict | None:
    """
    Получает данные из кэша.
    """
    if not _cache_enabled:
        return None

    conn = _get_connection()

    try:
        row = conn.execute(
            "SELECT data, timestamp FROM cache WHERE ip = ? AND collector = ?",
            (ip, collector),
        ).fetchone()

        if row:
            age = time.time() - row["timestamp"]
            if age <= _ttl_map.get(collector, 86400):
                return json.loads(row["data"])
    except Exception as e:
        pass  # Игнорируем ошибки чтения

    return None


def set(ip: str, collector: str, data: dict) -> None:
    """
    Сохраняет данные в кэш с retry-логикой.
    """
    if not _cache_enabled:
        return

    conn = _get_connection()

    # Retry с exponential backoff
    for attempt in range(_max_retries):
        try:
            conn.execute(
                "INSERT OR REPLACE INTO cache (ip, collector, timestamp, data) VALUES (?, ?, ?, ?)",
                (ip, collector, time.time(), json.dumps(data, default=str)),
            )
            conn.commit()
            return
        except sqlite3.OperationalError as e:
            if "locked" in str(e) and attempt < _max_retries - 1:
                time.sleep(0.1 * (2 ** attempt))  # 0.1s, 0.2s, 0.4s
                continue
            # Если не удалось после всех попыток — игнорируем
            break
        except Exception:
            break


def clear() -> None:
    """
    Очистить весь кэш.
    """
    conn = _get_connection()
    try:
        conn.execute("DELETE FROM cache")
        conn.commit()
    except Exception:
        pass
