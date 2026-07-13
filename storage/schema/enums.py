from enum import Enum

class DeviceStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"

class DeviceType(str, Enum):
    UNKNOWN = "UNKNOWN"
    PHONE = "PHONE"
    TABLET = "TABLET"
    LAPTOP = "LAPTOP"
    DESKTOP = "DESKTOP"
    PRINTER = "PRINTER"
    CAMERA = "CAMERA"
    ROUTER = "ROUTER"
    SWITCH = "SWITCH"
    ACCESS_POINT = "ACCESS_POINT"
    TV = "TV"
    IOT = "IOT"
    SERVER = "SERVER"

class ObservationType(str, Enum):
    STRING = "STRING"
    INTEGER = "INTEGER"
    BOOLEAN = "BOOLEAN"
    JSON = "JSON"

class CollectorStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    SKIPPED = "SKIPPED"

class ScanStatus(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"

class CapabilityType(str, Enum):
    HTTP = "HTTP"
    HTTPS = "HTTPS"
    SSH = "SSH"
    TELNET = "TELNET"
    SNMP = "SNMP"
    SSDP = "SSDP"
    MDNS = "MDNS"
    ICMP = "ICMP"
    WEB = "WEB"
    FTP = "FTP"
    SMB = "SMB"
