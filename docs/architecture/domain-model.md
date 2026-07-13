# SISU Domain Specification v2.0

**Официальный архитектурный контракт проекта**  
**Дата:** 2026-07-13  
**Статус:** Активная спецификация

---

## 1. Философские принципы (The Contract)

### Golden Rule
**Никакая информация никогда не изменяется задним числом.**

Если вчера было `TTL = 64`, то завтра мы не исправляем старую запись. Мы создаём новую. История всегда остаётся историей.

### Core Principle
**SISU хранит не устройства. Она хранит наблюдения.**

Из наблюдений строятся снимки.  
Из снимков строится история устройства.

### Правила реализации

1. **Чистота:** Только стандартная библиотека Python (`dataclasses`, `datetime`, `uuid`, `enum`, `typing`).
2. **Неизменяемость:** Все сущности — `@dataclass(frozen=True)`.
3. **Отсутствие логики хранения:** Никакого SQL, SQLite, SQLAlchemy.
4. **UUID-only связи:** Никаких прямых ссылок между сущностями.
5. **Confidence: 0..100** — контракт всей системы.
6. **Vendor = str** — не Enum (OUI обновляется).
7. **DeviceType = Enum** — строгая типизация.
8. **Observation.value** — всегда строка. Интерпретация через `ObservationType`.

---

## 2. Архитектура зависимостей

External World (Collectors, Correlation Engine)
|
v
SISU Domain Model (storage/schema)
|
+---------------+---------------+
| | |
v v v
SQLite REST API Web UI
12345
Scan (корневая сущность)
|
+-- Snapshot (один запуск = один Snapshot на устройство)
| |
| +-- Observation (атомарные факты)
| +-- Evidence (обоснования решений)
| +-- Capability (возможности устройства)
|
+-- CollectorLog (журнал работы сборщиков)
Device (живет отдельно, связан через UUID)
|
+-- Identity (ядро идентификации)
+-- Snapshot (множество снимков во времени)
+-- Session (сетевая активность)

---

## 3. Иерархия сущностей
Scan (корневая сущность)
|
+-- Snapshot (один запуск = один Snapshot на устройство)
| |
| +-- Observation (атомарные факты)
| +-- Evidence (обоснования решений)
| +-- Capability (возможности устройства)
|
+-- CollectorLog (журнал работы сборщиков)
Device (живет отдельно, связан через UUID)
|
+-- Identity (ядро идентификации)
+-- Snapshot (множество снимков во времени)
+-- Session (сетевая активность)

---

## 4. Описание сущностей

### Scan (Корневая сущность)

Группирует все данные одного запуска мониторинга.

**Поля:**
- `id` (UUID) — уникальный идентификатор
- `started_at` (datetime) — время начала сканирования
- `finished_at` (datetime | None) — время завершения
- `collector_version` (str) — версия SISU
- `duration_ms` (float) — длительность в миллисекундах
- `devices_found` (int) — количество найденных устройств
- `status` (Enum: SUCCESS, PARTIAL, FAILED) — статус завершения

---

### Device (Паспорт устройства)

**Только неизменяемое.** Vendor и device_type вычисляются из последних данных.

**Поля:**
- `id` (UUID) — уникальный идентификатор
- `mac` (str) — MAC-адрес
- `first_seen` (datetime) — дата первого обнаружения
- `last_seen` (datetime) — дата последнего обнаружения
- `status` (Enum: ACTIVE, ARCHIVED) — статус устройства

**Принцип:** Device существует всегда, никогда не удаляется (только ARCHIVED).

---

### Identity (Ядро идентификации)

Агрегирует ключевые признаки для "узнавания" устройства при смене IP или временной недоступности.

**Поля:**
- `id` (UUID) — уникальный идентификатор
- `device_id` (UUID) — связь с Device
- `mac` (str) — MAC-адрес
- `vendor` (str) — производитель (строка, не Enum)
- `device_type` (Enum DeviceType) — тип устройства
- `fingerprint_hash` (str) — хэш стабильных признаков
- `base_confidence` (int, 0..100) — базовая уверенность

---

### Snapshot (Снимок состояния)

"Фотография" устройства в конкретный момент времени. Один запуск мониторинга = один Snapshot на устройство.

**Поля:**
- `id` (UUID) — уникальный идентификатор
- `scan_id` (UUID) — связь с Scan
- `device_id` (UUID) — связь с Device
- `timestamp` (datetime) — время снимка
- `ip` (str) — IP-адрес
- `hostname` (str) — имя хоста
- `os` (str) — операционная система
- `model` (str) — модель устройства
- `device_type` (Enum DeviceType) — тип устройства
- `confidence` (int, 0..100) — общая уверенность

---

### Observation (Атомарный факт)

Универсальная сущность (EAV-паттерн). **value всегда строка.** Интерпретация через ObservationType.

**Поля:**
- `id` (UUID) — уникальный идентификатор
- `snapshot_id` (UUID) — связь с Snapshot
- `source` (Enum Source) — источник данных
- `key` (str) — ключ (например: "http.server", "ttl")
- `value` (str) — значение (всегда строка)
- `obs_type` (Enum: STRING, INTEGER, BOOLEAN, JSON) — тип значения
- `unit` (str | None) — единица измерения (например: "C", "MB", None)
- `confidence` (int, 0..100) — уверенность в факте

**Контракт:** Все значения сериализуются в строку. Интерпретация выполняется только через ObservationType.

**Примеры:**

TTL:
- source=TTL, key="ttl", value="64", obs_type=INTEGER, unit=None, confidence=40

HTTP Server:
- source=HTTP, key="http.server", value="nginx", obs_type=STRING, unit=None, confidence=90

Temperature:
- source=SNMP, key="temperature", value="52", obs_type=INTEGER, unit="C", confidence=100

---

### Evidence (Обоснование решения)

Объясняет, *почему* Correlation Engine принял то или иное решение для данного Snapshot.

**Поля:**
- `id` (UUID) — уникальный идентификатор
- `snapshot_id` (UUID) — связь с Snapshot
- `description` (str) — описание (например: "Rule: android_xiaomi")
- `contribution` (int) — вклад в общий confidence
- `source` (Enum Source) — источник
- `details` (str) — дополнительные детали

---

### Capability (Возможности устройства)

**Одна запись = одна возможность.** Подтверждённые протоколы/сервисы.

**Поля:**
- `id` (UUID) — уникальный идентификатор
- `snapshot_id` (UUID) — связь с Snapshot
- `capability` (Enum CapabilityType) — тип возможности
- `confidence` (int, 0..100) — уверенность

---

### Session (Сетевая сессия)

Агрегированные данные о трафике за период.

**Поля:**
- `id` (UUID) — уникальный идентификатор
- `device_id` (UUID) — связь с Device
- `source` (Enum Source) — источник данных (например: NETFLOW, SNMP)
- `start_time` (datetime) — начало сессии
- `end_time` (datetime | None) — конец сессии
- `duration` (float) — длительность в секундах
- `bytes_in` (int) — входящий трафик в байтах
- `bytes_out` (int) — исходящий трафик в байтах
- `flows` (int) — количество потоков

---

### CollectorLog (Журнал работы сборщиков)

Метрики здоровья системы SISU.

**Поля:**
- `id` (UUID) — уникальный идентификатор
- `scan_id` (UUID) — связь с Scan
- `collector_name` (str) — имя коллектора
- `started_at` (datetime) — время начала
- `finished_at` (datetime) — время завершения
- `duration_ms` (float) — длительность в миллисекундах
- `objects_processed` (int) — количество обработанных объектов
- `status` (Enum: SUCCESS, FAILED, TIMEOUT, SKIPPED) — статус
- `warnings` (int) — количество предупреждений
- `error_message` (str) — сообщение об ошибке

---

## 5. Enum определения

### DeviceType
UNKNOWN, PHONE, TABLET, LAPTOP, DESKTOP, PRINTER, CAMERA, ROUTER, SWITCH, ACCESS_POINT, TV, IOT, SERVER

### Source
ARP, DNS, MDNS, TTL, TCP, HTTP, SSDP, SNMP, PING, NETFLOW, MANUAL, IMPORT, UNKNOWN

### CapabilityType
HTTP, HTTPS, SSH, TELNET, SNMP, SSDP, MDNS, ICMP, WEB, FTP, SMB

### DeviceStatus
ACTIVE, ARCHIVED

### ObservationType
STRING, INTEGER, BOOLEAN, JSON

### CollectorStatus
SUCCESS, FAILED, TIMEOUT, SKIPPED

### ScanStatus
SUCCESS, PARTIAL, FAILED

---

## 6. Версионирование

Файл `storage/schema/version.py`:

```python
DOMAIN_MODEL_VERSION = "2.0"
7. Контракты и правила
Confidence: 0..100
Все поля confidence должны находиться в диапазоне 0..100. Валидация выполняется на уровне Repository (не в dataclass).
UUID-only связи
Никакие сущности не содержат прямых ссылок друг на друга. Связи существуют только через UUID.
Неизменяемость
Все сущности используют @dataclass(frozen=True). Данные не мутируются, создаются новые снимки.
Vendor = str
Vendor — строка, не Enum. OUI обновляется постоянно, Enum будет ограничением.
DeviceType = Enum
DeviceType — строгая типизация через Enum для исключения хаоса ("Router"/"ROUTER"/"router").
Observation.value — всегда строка
Все значения сериализуются в строку. Интерпретация выполняется только через ObservationType.
8. Вердикт
Спецификация SISU Domain Specification v2.0 завершена.
Этот документ является официальным архитектурным контрактом проекта и должен быть зафиксирован в репозитории перед написанием кода.
9. История изменений
v2.0 (2026-07-13)
Добавлена корневая сущность Scan
Device упрощён до паспорта (убран vendor, device_type)
Добавлен scan_id в Snapshot
Добавлен unit в Observation
Capability как отдельные записи (одна запись = одна возможность)
Добавлен source в Session
Добавлен warnings в CollectorLog
Введён Golden Rule (никаких изменений задним числом)
Vendor = str, DeviceType = Enum
v1.0 (2026-07-13)
Первоначальная версия
Device включал vendor и device_type
Отсутствовала корневая сущность Scan
