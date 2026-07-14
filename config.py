"""
Repeater Monitor
config.py

Пользовательская конфигурация проекта.
"""

from pathlib import Path


class App:

    NAME = "Repeater Monitor"
    VERSION = "1.0.0"

    DEBUG = False
    VERBOSE = True
    DEBUG_LEVEL = 3  # 0: только отчёт, 1: +timing, 2: +raw_data, 3: +все заголовки

class Paths:

    BASE_DIR = Path(__file__).resolve().parent

    NFDUMP_DIR = Path("/var/nfdump")

    CACHE_DIR = BASE_DIR / "cache"
    LOG_DIR = BASE_DIR / "logs"
    REPORT_DIR = BASE_DIR / "reports"
    EXPORT_DIR = BASE_DIR / "exports"


class Cisco:

    IP = "192.168.0.1"

    COMMUNITY = "My_Navi_RO_String"

    PORT = 161

    TIMEOUT = 5

    RETRIES = 2


class Network:

    NAME = "VLAN20"

    SUBNET = "192.168.1.0/24"

    PREFIX = "192.168.1."


class NetFlow:

    ACTIVE_WINDOW_HOURS = 24

    FORMAT = "csv"

    TOP = 0


class Thresholds:

    MIN_ONLINE_MINUTES = 30

    LOW_MB_PER_HOUR = 20

    NORMAL_MB_PER_HOUR = 100

    MIN_TOTAL_MB = 10

    SUSPECT_FLOWS_THRESHOLD = 100

    HIGH_FLOWS_THRESHOLD = 300


class Detection:

    ACTIVE_ONLY = True

    REQUIRE_MAC = True

    SORT_SUSPECTS_FIRST = True

    EXCLUDED_IPS = {

        "192.168.1.1",

    }


class Retention:

    FLOW_DAYS = 3

    CACHE_DAYS = 7

    LOG_DAYS = 30


class Export:

    TXT = True

    CSV = True

    JSON = True


class Fingerprint:

    MDNS_TIMEOUT = 0.7

    DNS_WORKERS = 16

    TTL_WORKERS = 32

    TTL_TIMEOUT = 1.0

    TTL_COUNT = 1

    TCP_WORKERS = 64

    TCP_TIMEOUT = 0.5

    TCP_MAX_CONNECTIONS_PER_HOST = 6

    HTTP_WORKERS = 32

    HTTP_TIMEOUT = 2.0

    HTTP_MAX_BODY_SIZE = 8192  # 8 KB

    CACHE_ENABLED = True
    CACHE_TTL_TTL = 3600      # 1 час
    CACHE_TTL_TCP = 86400     # 24 часа
    CACHE_TTL_HTTP = 86400    # 24 часа
    CACHE_TTL_SSDP = 43200    # 12 часов
    CACHE_TTL_SNMP = 86400    # 24 часа

    HTTP_MAX_WORKERS_PER_DEVICE = 4  # макс потоков на одно устройство

    # ---------------------------------------------------------
    # SSDP / UPnP
    # ---------------------------------------------------------
    SSDP_ENABLED = True
    SSDP_TIMEOUT = 3.0           # Таймаут ожидания ответов
    SSDP_MX = 3                   # Максимальное время ответа (MX в M-SEARCH)
    SSDP_MULTICAST = "239.255.255.250"
    SSDP_PORT = 1900
    SSDP_FETCH_DESCRIPTION = True # Делать ли GET к LOCATION для XML
    SSDP_DESCRIPTION_TIMEOUT = 2.0 # Таймаут для GET описания

    # ---------------------------------------------------------
    # SNMP (Generic Collector)
    # ---------------------------------------------------------
    SNMP_ENABLED = True
    SNMP_VERSION = "v2c"
    SNMP_COMMUNITIES = [
        "My_Navi_RO_String",
        "public",
        "private",
        "monitor",
    ]
    SNMP_PORT = 161
    SNMP_TIMEOUT = 0.3          # Было 1.0 — уменьшаем
    SNMP_RETRIES = 0            # Было 0 — оставляем
    SNMP_WORKERS = 64           # Было 64 — оставляем
    SNMP_DEVICE_TIMEOUT = 0.5   # Было 2.0 — уменьшаем
    SNMP_SKIP_IF_NO_PING = True # Пропускать SNMP, если нет ping

    # SNMP OID (только сбор данных, без интерпретации)
    SNMP_OID_SYS_DESCR = "1.3.6.1.2.1.1.1.0"
    SNMP_OID_SYS_OBJECT_ID = "1.3.6.1.2.1.1.2.0"
    SNMP_OID_SYS_UP_TIME = "1.3.6.1.2.1.1.3.0"
    SNMP_OID_SYS_NAME = "1.3.6.1.2.1.1.5.0"
    SNMP_OID_SYS_SERVICES = "1.3.6.1.2.1.1.7.0"
    SNMP_OID_SYS_LOCATION = "1.3.6.1.2.1.1.6.0"  # <-- ДОБАВЛЕНО
    SNMP_OID_SYS_CONTACT = "1.3.6.1.2.1.1.4.0"   # <-- ДОБАВЛЕНО
