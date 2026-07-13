from enum import Enum

class Source(str, Enum):
    ARP = "ARP"
    DNS = "DNS"
    MDNS = "MDNS"
    TTL = "TTL"
    TCP = "TCP"
    HTTP = "HTTP"
    SSDP = "SSDP"
    SNMP = "SNMP"
    PING = "PING"
    NETFLOW = "NETFLOW"
    MANUAL = "MANUAL"
    IMPORT = "IMPORT"
    UNKNOWN = "UNKNOWN"
