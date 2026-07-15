#!/usr/bin/env python3
"""
History Service — единая точка доступа к историческим данным.
Только чтение, никакой записи. Никакого анализа.
Не знает о специфичных контроллерах (Omada, UniFi и т.д.).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from . import queries
from .models import (
    SnapshotRecord,
    ObservationRecord,
    EventRecord,
    EvidenceRecord,
    CapabilityRecord,
    DeviceHistory,
)


class HistoryService:
    """
    Сервис для работы с историческими данными.
    Предоставляет единый API для всех движков.
    """

    def __init__(self, db_connection):
        self.db = db_connection
        self._cache = {}

    def _parse_timestamp(self, ts_str: str) -> datetime:
        """Парсит timestamp из БД в datetime."""
        try:
            return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except:
            return datetime.now()

    def _execute_query(self, query: str, params: tuple = ()) -> list[tuple]:
        """Выполняет SQL-запрос и возвращает результаты."""
        cursor = self.db.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

    # =========================================================================
    # Базовые методы
    # =========================================================================

    def get_device_info(self, device_id: str) -> dict[str, Any] | None:
        """Получить базовую информацию об устройстве."""
        cache_key = f"device_info:{device_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        rows = self._execute_query(queries.GET_DEVICE_INFO, (device_id,))
        if not rows:
            return None

        row = rows[0]
        result = {
            "id": row[0],
            "mac": row[1],
            "first_seen": self._parse_timestamp(row[2]),
            "last_seen": self._parse_timestamp(row[3]),
            "status": row[4],
        }

        self._cache[cache_key] = result
        return result

    def get_device_history(self, device_id: str) -> DeviceHistory:
        """
        Получить историю устройства (ленивая загрузка).
        Данные загружаются только при обращении к свойствам.
        """
        device_info = self.get_device_info(device_id)
        if not device_info:
            raise ValueError(f"Device {device_id} not found")

        return DeviceHistory(
            device_id=device_id,
            mac=device_info["mac"],
            first_seen=device_info["first_seen"],
            last_seen=device_info["last_seen"],
            _service=self,  # Передаем ссылку для ленивой загрузки
        )

    # =========================================================================
    # Snapshot'ы
    # =========================================================================

    def get_snapshots(self, device_id: str) -> list[SnapshotRecord]:
        """Получить все snapshot'ы устройства."""
        rows = self._execute_query(queries.GET_SNAPSHOTS, (device_id,))
        return [
            SnapshotRecord(
                id=row[0],
                scan_id=row[1],
                device_id=row[2],
                timestamp=self._parse_timestamp(row[3]),
                ip=row[4],
                hostname=row[5],
                os=row[6],
                model=row[7],
                device_type=row[8],
                confidence=row[9],
            )
            for row in rows
        ]

    def get_last_snapshot(self, device_id: str) -> SnapshotRecord | None:
        """Получить последний snapshot устройства."""
        cache_key = f"last_snapshot:{device_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        rows = self._execute_query(queries.GET_LAST_SNAPSHOT, (device_id,))
        if not rows:
            return None

        row = rows[0]
        result = SnapshotRecord(
            id=row[0],
            scan_id=row[1],
            device_id=row[2],
            timestamp=self._parse_timestamp(row[3]),
            ip=row[4],
            hostname=row[5],
            os=row[6],
            model=row[7],
            device_type=row[8],
            confidence=row[9],
        )

        self._cache[cache_key] = result
        return result

    def get_first_seen(self, device_id: str) -> datetime | None:
        """Когда устройство появилось впервые."""
        rows = self._execute_query(queries.GET_FIRST_SEEN, (device_id,))
        if not rows or not rows[0][0]:
            return None
        return self._parse_timestamp(rows[0][0])

    def get_last_seen(self, device_id: str) -> datetime | None:
        """Последнее появление устройства."""
        rows = self._execute_query(queries.GET_LAST_SEEN, (device_id,))
        if not rows or not rows[0][0]:
            return None
        return self._parse_timestamp(rows[0][0])

    # =========================================================================
    # Observations
    # =========================================================================

    def get_observations(
        self,
        device_id: str,
        source: str | None = None,
        key: str | None = None,
    ) -> list[ObservationRecord]:
        """Получить все observations устройства с опциональной фильтрацией."""
        if source or key:
            rows = self._execute_query(
                queries.GET_OBSERVATIONS_FILTERED,
                (device_id, source, source, key, key),
            )
        else:
            rows = self._execute_query(queries.GET_OBSERVATIONS, (device_id,))

        return [
            ObservationRecord(
                id=row[0],
                snapshot_id=row[1],
                source=row[2],
                key=row[3],
                value=row[4],  # JSON-строка
                obs_type=row[5],
                unit=row[6],
                confidence=row[7],
                timestamp=self._parse_timestamp(row[8]) if row[8] else None,
            )
            for row in rows
        ]

    # =========================================================================
    # История изменений
    # =========================================================================

    def get_ip_history(self, device_id: str) -> list[dict[str, Any]]:
        """История IP-адресов устройства."""
        rows = self._execute_query(queries.GET_IP_HISTORY, (device_id,))
        return [
            {
                "timestamp": self._parse_timestamp(row[0]),
                "ip": row[1],
            }
            for row in rows
        ]

    def get_mac_history(self, device_id: str) -> list[dict[str, Any]]:
        """История MAC-адресов."""
        rows = self._execute_query(queries.GET_MAC_HISTORY, (device_id,))
        return [
            {
                "mac": row[0],
                "first_seen": self._parse_timestamp(row[1]),
                "last_seen": self._parse_timestamp(row[2]),
            }
            for row in rows
        ]

    def get_hostname_history(self, device_id: str) -> list[dict[str, Any]]:
        """История hostname'ов устройства."""
        rows = self._execute_query(queries.GET_HOSTNAME_HISTORY, (device_id,))
        return [
            {
                "timestamp": self._parse_timestamp(row[0]),
                "hostname": row[1],
            }
            for row in rows
        ]

    def get_vendor_history(self, device_id: str) -> list[dict[str, Any]]:
        """История vendor'ов (из identity table)."""
        rows = self._execute_query(queries.GET_VENDOR_HISTORY, (device_id,))
        return [
            {
                "vendor": row[0],
                "mac": row[1],
            }
            for row in rows
        ]

    # =========================================================================
    # События и доказательства
    # =========================================================================

    def get_events(self, device_id: str) -> list[EventRecord]:
        """Все события устройства."""
        rows = self._execute_query(queries.GET_EVENTS, (device_id,))
        return [
            EventRecord(
                event_id=row[0],
                device_id=row[1],
                snapshot_id=row[2],
                timestamp=self._parse_timestamp(row[3]),
                type=row[4],
                severity=row[5],
                title=row[6],
                description=row[7],
                details=row[8],
                acknowledged=bool(row[9]),
            )
            for row in rows
        ]

    def get_evidence(self, device_id: str) -> list[EvidenceRecord]:
        """Все evidence устройства."""
        rows = self._execute_query(queries.GET_EVIDENCE, (device_id,))
        return [
            EvidenceRecord(
                id=row[0],
                snapshot_id=row[1],
                description=row[2],
                contribution=row[3],
                source=row[4],
                details=row[5],
                timestamp=self._parse_timestamp(row[6]) if row[6] else None,
            )
            for row in rows
        ]

    def get_capabilities(self, device_id: str) -> list[CapabilityRecord]:
        """Все capabilities устройства."""
        rows = self._execute_query(queries.GET_CAPABILITIES, (device_id,))
        return [
            CapabilityRecord(
                id=row[0],
                snapshot_id=row[1],
                capability=row[2],
                confidence=row[3],
                timestamp=self._parse_timestamp(row[4]) if row[4] else None,
            )
            for row in rows
        ]

    # =========================================================================
    # Управление кэшем
    # =========================================================================

    def clear_cache(self):
        """Очистить кэш."""
        self._cache.clear()
