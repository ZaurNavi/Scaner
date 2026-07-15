#!/usr/bin/env python3
"""
SQL-запросы для History Service.
Все запросы вынесены отдельно для упрощения поддержки.
"""

# Получить базовую информацию об устройстве
GET_DEVICE_INFO = """
SELECT id, mac, first_seen, last_seen, status
FROM device
WHERE id = ?
"""

# Получить все snapshot'ы устройства
GET_SNAPSHOTS = """
SELECT id, scan_id, device_id, timestamp, ip, 
       hostname, os, model, device_type, confidence
FROM snapshot
WHERE device_id = ?
ORDER BY timestamp ASC
"""

# Получить последний snapshot устройства
GET_LAST_SNAPSHOT = """
SELECT id, scan_id, device_id, timestamp, ip, 
       hostname, os, model, device_type, confidence
FROM snapshot
WHERE device_id = ?
ORDER BY timestamp DESC
LIMIT 1
"""

# Получить первое появление устройства
GET_FIRST_SEEN = """
SELECT MIN(timestamp) as first_seen
FROM snapshot
WHERE device_id = ?
"""

# Получить последнее появление устройства
GET_LAST_SEEN = """
SELECT MAX(timestamp) as last_seen
FROM snapshot
WHERE device_id = ?
"""

# Получить все observations устройства (через snapshot'ы)
GET_OBSERVATIONS = """
SELECT o.id, o.snapshot_id, o.source, o.key, o.value, 
       o.obs_type, o.unit, o.confidence, s.timestamp
FROM observation o
JOIN snapshot s ON o.snapshot_id = s.id
WHERE s.device_id = ?
ORDER BY s.timestamp ASC, o.source ASC
"""

# Получить observations с фильтрацией по source и key
GET_OBSERVATIONS_FILTERED = """
SELECT o.id, o.snapshot_id, o.source, o.key, o.value, 
       o.obs_type, o.unit, o.confidence, s.timestamp
FROM observation o
JOIN snapshot s ON o.snapshot_id = s.id
WHERE s.device_id = ?
  AND (? IS NULL OR o.source = ?)
  AND (? IS NULL OR o.key = ?)
ORDER BY s.timestamp ASC
"""

# Получить историю IP-адресов устройства
GET_IP_HISTORY = """
SELECT DISTINCT timestamp, ip
FROM snapshot
WHERE device_id = ?
ORDER BY timestamp ASC
"""

# Получить историю MAC-адресов (из device table)
GET_MAC_HISTORY = """
SELECT DISTINCT mac, first_seen, last_seen
FROM device
WHERE id = ?
"""

# Получить историю hostname'ов устройства
GET_HOSTNAME_HISTORY = """
SELECT DISTINCT timestamp, hostname
FROM snapshot
WHERE device_id = ? AND hostname IS NOT NULL AND hostname != ''
ORDER BY timestamp ASC
"""

# Получить историю vendor'ов (из identity table)
GET_VENDOR_HISTORY = """
SELECT DISTINCT vendor, mac
FROM identity
WHERE device_id = ?
ORDER BY mac
"""

# Получить все события устройства
GET_EVENTS = """
SELECT event_id, device_id, snapshot_id, timestamp, type, 
       severity, title, description, details, acknowledged
FROM event
WHERE device_id = ?
ORDER BY timestamp ASC
"""

# Получить все evidence устройства
GET_EVIDENCE = """
SELECT e.id, e.snapshot_id, e.description, e.contribution, 
       e.source, e.details, s.timestamp
FROM evidence e
JOIN snapshot s ON e.snapshot_id = s.id
WHERE s.device_id = ?
ORDER BY s.timestamp ASC
"""

# Получить все capabilities устройства
GET_CAPABILITIES = """
SELECT c.id, c.snapshot_id, c.capability, c.confidence, s.timestamp
FROM capability c
JOIN snapshot s ON c.snapshot_id = s.id
WHERE s.device_id = ?
ORDER BY s.timestamp ASC
"""
