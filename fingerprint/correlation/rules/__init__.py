"""
Правила корреляции — разбиты по категориям устройств.
"""

from .android import ANDROID_RULES
from .routers import ROUTER_RULES
from .printers import PRINTER_RULES
from .cameras import CAMERA_RULES
from .windows import WINDOWS_RULES
from .linux import LINUX_RULES
from .apple import APPLE_RULES
from .iot import IOT_RULES
from .http_devices import HTTP_DEVICE_RULES
from .ssdp_devices import SSDP_DEVICE_RULES
from .snmp_devices import SNMP_DEVICE_RULES
from .negative import NEGATIVE_RULES

# Все правила в одном списке, отсортированы по priority
ALL_RULES = (
    ROUTER_RULES +
    PRINTER_RULES +
    CAMERA_RULES +
    ANDROID_RULES +
    APPLE_RULES +
    WINDOWS_RULES +
    LINUX_RULES +
    IOT_RULES +
    HTTP_DEVICE_RULES +
    SSDP_DEVICE_RULES +
    SNMP_DEVICE_RULES +
    NEGATIVE_RULES  # Negative rules — самые низкие по приоритету
)

# Сортируем по priority (убывание)
ALL_RULES.sort(key=lambda r: r.priority, reverse=True)

__all__ = ["ALL_RULES"]
