from enum import Enum

class DeviceType(str, Enum):
    ROUTER = "Router"
    SMARTPHONE = "Smartphone"
    PRINTER = "Printer"
    IP_CAMERA = "IP Camera"
    NAS = "NAS"
    PC_SERVER = "PC/Server"
    LAPTOP = "Laptop"
    TABLET = "Tablet"
    MEDIA_PLAYER = "Media Player"
    MEDIA_SERVER = "Media Server"
    IOT_DEVICE = "IoT Device"
    NETWORK_DEVICE = "Network Device"
    SERVER = "Server"
    ACCESS_POINT = "Access Point"
    UNIFI_CONTROLLER = "UniFi Controller"
    UNKNOWN = "Unknown"

class OS(str, Enum):
    ANDROID = "Android"
    IOS = "iOS"
    LINUX = "Linux"
    WINDOWS = "Windows"
    MACOS = "macOS"
    ROUTEROS = "RouterOS"
    OPENWRT = "OpenWrt"
    KEENETIC_OS = "KeeneticOS"
    DSM = "DSM"  # Synology
    QTS = "QTS"   # QNAP
    EMBEDDED = "Embedded"
    EMBEDDED_LINUX = "Embedded Linux"
    UNKNOWN = "Unknown"
