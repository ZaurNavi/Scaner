from enum import Enum


class EventType(str, Enum):
    """Типы событий, которые может обнаружить Event Engine."""
    FIRST_SEEN = "FIRST_SEEN"
    IP_CHANGED = "IP_CHANGED"
    HOSTNAME_CHANGED = "HOSTNAME_CHANGED"
    VENDOR_DISCOVERED = "VENDOR_DISCOVERED"
    DEVICE_CLASSIFIED = "DEVICE_CLASSIFIED"


class Severity(str, Enum):
    """Серьёзность события."""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
