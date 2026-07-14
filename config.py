"""
Repeater Monitor
config.py

Пользовательская конфигурация проекта.
Чувствительные данные (пароли, токены) читаются из переменных окружения (.env файл).
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Загружаем переменные из .env файла при старте приложения
load_dotenv()


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
    CACHE_TTL_DHCP = 300      # 5 минут (DHCP leases меняются чаще)

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

    # ---------------------------------------------------------
    # SNMP OID: System (базовые)
    # ---------------------------------------------------------
    SNMP_OID_SYS_DESCR = "1.3.6.1.2.1.1.1.0"
    SNMP_OID_SYS_OBJECT_ID = "1.3.6.1.2.1.1.2.0"
    SNMP_OID_SYS_UP_TIME = "1.3.6.1.2.1.1.3.0"
    SNMP_OID_SYS_CONTACT = "1.3.6.1.2.1.1.4.0"
    SNMP_OID_SYS_NAME = "1.3.6.1.2.1.1.5.0"
    SNMP_OID_SYS_LOCATION = "1.3.6.1.2.1.1.6.0"
    SNMP_OID_SYS_SERVICES = "1.3.6.1.2.1.1.7.0"

    # ---------------------------------------------------------
    # SNMP OID: Interfaces (IF-MIB)
    # ---------------------------------------------------------
    SNMP_OID_IF_NUMBER = "1.3.6.1.2.1.2.1.0"          # ifNumber (количество интерфейсов)
    SNMP_OID_IF_TABLE = "1.3.6.1.2.1.2.2"             # ifTable (корневой OID)
    SNMP_OID_IF_DESCR = "1.3.6.1.2.1.2.2.1.2"         # ifDescr
    SNMP_OID_IF_TYPE = "1.3.6.1.2.1.2.2.1.3"          # ifType
    SNMP_OID_IF_MTU = "1.3.6.1.2.1.2.2.1.4"           # ifMTU
    SNMP_OID_IF_SPEED = "1.3.6.1.2.1.2.2.1.5"         # ifSpeed
    SNMP_OID_IF_PHYS_ADDRESS = "1.3.6.1.2.1.2.2.1.6"  # ifPhysAddress (MAC интерфейса)
    SNMP_OID_IF_ADMIN_STATUS = "1.3.6.1.2.1.2.2.1.7"  # ifAdminStatus
    SNMP_OID_IF_OPER_STATUS = "1.3.6.1.2.1.2.2.1.8"   # ifOperStatus
    SNMP_OID_IF_ALIAS = "1.3.6.1.2.1.31.1.1.1.18"     # ifAlias (описание интерфейса)

    # ---------------------------------------------------------
    # SNMP OID: Bridge MIB (для Switch Port Collector)
    # ---------------------------------------------------------
    SNMP_OID_DOT1D_BASE_BRIDGE_ADDRESS = "1.3.6.1.2.1.17.1.1.0"  # MAC коммутатора
    SNMP_OID_DOT1D_TP_FDB_PORT = "1.3.6.1.2.1.17.4.3.1.2"        # MAC → Bridge Port
    SNMP_OID_DOT1D_BASE_PORT_IF_INDEX = "1.3.6.1.2.1.17.1.4.1.2" # Bridge Port → ifIndex

    # ---------------------------------------------------------
    # SNMP OID: LLDP (LLDP-MIB)
    # ---------------------------------------------------------
    SNMP_OID_LLDP_LOC_SYS_NAME = "1.0.8802.1.1.2.1.3.2.0"        # lldpLocSysName
    SNMP_OID_LLDP_REM_TABLE = "1.0.8802.1.1.2.1.4.1.1"           # lldpRemTable
    SNMP_OID_LLDP_REM_SYS_NAME = "1.0.8802.1.1.2.1.4.1.1.9"      # lldpRemSysName
    SNMP_OID_LLDP_REM_PORT_ID = "1.0.8802.1.1.2.1.4.1.1.7"       # lldpRemPortId

    # ---------------------------------------------------------
    # SNMP OID: Entity MIB (физические компоненты)
    # ---------------------------------------------------------
    SNMP_OID_ENT_PHYSICAL_TABLE = "1.3.6.1.2.1.47.1.1.1.1"       # entPhysicalEntry
    SNMP_OID_ENT_PHYSICAL_DESCR = "1.3.6.1.2.1.47.1.1.1.1.2"     # entPhysicalDescr
    SNMP_OID_ENT_PHYSICAL_MODEL = "1.3.6.1.2.1.47.1.1.1.1.13"    # entPhysicalModelName
    SNMP_OID_ENT_PHYSICAL_SERIAL = "1.3.6.1.2.1.47.1.1.1.1.11"   # entPhysicalSerialNum


class CiscoDHCP:
    """
    Конфигурация для получения DHCP-leases с Cisco 3845 через SSH.
    
    Все чувствительные данные (пароли, пути к ключам) читаются из переменных
    окружения через файл .env в корне проекта.
    
    Файл .env должен быть добавлен в .gitignore и НЕ коммититься в Git.
    Для шаблона используйте .env.example.
    """
    
    IP = os.getenv("CISCO_DHCP_IP", "192.168.0.1")
    PORT = int(os.getenv("CISCO_DHCP_PORT", "22"))
    
    # Аутентификация (читается из .env)
    USERNAME = os.getenv("CISCO_DHCP_USERNAME", "admin")
    PASSWORD = os.getenv("CISCO_DHCP_PASSWORD", "")  # Пароль SSH
    SSH_KEY_PATH = os.getenv("CISCO_DHCP_SSH_KEY_PATH", "")  # Путь к приватному ключу
    
    ENABLE_PASSWORD = os.getenv("CISCO_DHCP_ENABLE_PASSWORD", "")
    
    TIMEOUT = int(os.getenv("CISCO_DHCP_TIMEOUT", "10"))
    CACHE_TTL = int(os.getenv("CISCO_DHCP_CACHE_TTL", "300"))  # 5 минут
    
    @classmethod
    def is_configured(cls) -> bool:
        """
        Проверяет, настроены ли учетные данные для подключения к Cisco.
        Возвращает True, если задан хотя бы пароль или путь к SSH-ключу.
        """
        return bool(cls.PASSWORD or cls.SSH_KEY_PATH)


class Telegram:
    """
    Конфигурация для Telegram-бота (будет использоваться в v1.6.0).
    Все данные читаются из .env.
    """
    
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
    
    @classmethod
    def is_configured(cls) -> bool:
        """Проверяет, настроен ли Telegram-бот."""
        return bool(cls.BOT_TOKEN and cls.CHAT_ID)
