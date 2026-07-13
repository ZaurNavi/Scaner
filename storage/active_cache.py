#!/usr/bin/env python3
"""
Active Cache для результатов коллекторов.
Использует WAL-режим для лучшей параллельной записи.
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

from config import Fingerprint, Paths

CACHE_DB = Paths.CACHE_DIR / "active_cache.db"

TTL_MAP = {
    "ttl": Fingerprint.CACHE_TTL_TTL,
    "tcp": Fingerprint.CACHE_TTL_TCP,
    "http": Fingerprint.CACHE_TTL_HTTP,
    "ssdp": Fingerprint.CACHE_TTL_SSDP,
    "snmp": Fingerprint.CACHE_TTL_SNMP,
}

# Глобальное соединение (одно на процесс)
_connection: sqlite3.Connection | None = None


def _get_connection() -> sqlite3.Connection:
    """
    Возвращает глобальное соединение с БД.
    Создаёт таблицу и включает WAL-режим при первом вызове.
    """
    global _connection

    if _connection is None:
        Paths.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        _connection = sqlite3.connect(str(CACHE_DB), check_same_thread=False)
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
        cutoff = time.time() - max(TTL_MAP.values())
        _connection.execute("DELETE FROM cache WHERE timestamp < ?", (cutoff,))
        _connection.commit()

    return _connection


def get(ip: str, collector: str) -> dict | None:
    """
    Получает данные из кэша.
    """
    if not Fingerprint.CACHE_ENABLED:
        return None

    conn = _get_connection()

    try:
        row = conn.execute(
            "SELECT data, timestamp FROM cache WHERE ip = ? AND collector = ?",
            (ip, collector),
        ).fetchone()

        if row:
            age = time.time() - row["timestamp"]
            if age <= TTL_MAP.get(collector, 86400):
                return json.loads(row["data"])
    except Exception as e:
        pass  # Игнорируем ошибки чтения

    return None


def set(ip: str, collector: str, data: dict) -> None:
    """
    Сохраняет данные в кэш с retry-логикой.
    """
    if not Fingerprint.CACHE_ENABLED:
        return

    conn = _get_connection()

    # Retry с exponential backoff
    max_retries = 3
    for attempt in range(max_retries):
        try:
            conn.execute(
                "INSERT OR REPLACE INTO cache (ip, collector, timestamp, data) VALUES (?, ?, ?, ?)",
                (ip, collector, time.time(), json.dumps(data, default=str)),
            )
            conn.commit()
            return
        except sqlite3.OperationalError as e:
            if "locked" in str(e) and attempt < max_retries - 1:
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
