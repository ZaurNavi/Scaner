#!/usr/bin/env python3
"""
Evidence — факты об устройстве, собранные из всех источников.
"""

from __future__ import annotations
from dataclasses import dataclass, field

from models import Device
from fingerprint.collectors.base import CollectedData


@dataclass
class Evidence:
    """
    Сырые факты об устройстве.
    """

    # Сетевое присутствие
    arp: bool = False
    flows: bool = False
    ping: bool | None = None
    ttl: int | None = None

    # TCP порты
    tcp_ports: dict = field(default_factory=dict)

    # HTTP данные
    http_headers: dict = field(default_factory=dict)
    http_server: str = ""
    http_title: str = ""
    http_body: str = ""

    # SSDP/UPnP данные
    ssdp_responded: bool = False
    ssdp_server: str = ""
    ssdp_location: str = ""
    ssdp_st: str = ""
    ssdp_usn: str = ""
    ssdp_manufacturer: str = ""
    ssdp_model_name: str = ""
    ssdp_friendly_name: str = ""
    ssdp_model_number: str = ""
    ssdp_serial_number: str = ""

    # SNMP данные (сырые факты — интерпретация в правилах)
    snmp_responded: bool = False
    snmp_community: str = ""
    snmp_sys_descr: str = ""
    snmp_sys_object_id: str = ""
    snmp_sys_up_time: int = 0
    snmp_sys_name: str = ""
    snmp_sys_services: int = 0

    # mDNS
    mdns: bool = False
    mdns_hostname: str = ""
    mdns_model: str = ""
    mdns_device_type: str = ""

    # DNS
    dns_hostname: str = ""

    # Идентификация
    vendor: str = ""
    hostname: str = ""
    mac: str = ""
    ip: str = ""

    # Трафик
    mb_per_hour: float = 0.0
    megabytes: float = 0.0
    flows_count: int = 0

    @classmethod
    def from_device(cls, device: Device, collected: CollectedData) -> Evidence:
        """
        Создаёт Evidence из Device и CollectedData.
        """
        e = cls()

        # Базовая информация
        e.ip = device.ip
        e.mac = device.mac
        e.vendor = device.vendor
        e.hostname = device.hostname
        e.mb_per_hour = device.mb_per_hour
        e.megabytes = device.megabytes
        e.flows_count = device.flows
        e.arp = True
        e.flows = device.flows > 0

        # TTL
        ttl_result = collected.sources.get("ttl")
        if ttl_result:
            e.ping = ttl_result.raw_data.get("alive", False)
            e.ttl = ttl_result.ttl

        # TCP
        tcp_result = collected.sources.get("tcp")
        if tcp_result:
            e.tcp_ports = tcp_result.services

        # HTTP
        http_result = collected.sources.get("http")
        if http_result:
            for port, data in http_result.services.items():
                if isinstance(data, dict):
                    e.http_server = data.get("server", "") or e.http_server
                    e.http_title = data.get("title", "") or e.http_title

        # SSDP/UPnP
        ssdp_result = collected.sources.get("ssdp")
        if ssdp_result:
            raw = ssdp_result.raw_data or {}
            e.ssdp_responded = raw.get("responded", False)
            if e.ssdp_responded:
                e.ssdp_server = raw.get("server", "")
                e.ssdp_location = raw.get("location", "")
                e.ssdp_st = raw.get("st", "")
                e.ssdp_usn = raw.get("usn", "")
                e.ssdp_manufacturer = raw.get("manufacturer", "")
                e.ssdp_model_name = raw.get("model_name", "")
                e.ssdp_friendly_name = raw.get("friendly_name", "")
                e.ssdp_model_number = raw.get("model_number", "")
                e.ssdp_serial_number = raw.get("serial_number", "")

        # SNMP (сырые данные — интерпретация в правилах)
        snmp_result = collected.sources.get("snmp")
        if snmp_result:
            raw = snmp_result.raw_data or {}
            e.snmp_responded = raw.get("responded", False)
            if e.snmp_responded:
                e.snmp_community = raw.get("community", "")
                e.snmp_sys_descr = raw.get("sysDescr", "")
                e.snmp_sys_object_id = raw.get("sysObjectID", "")
                e.snmp_sys_up_time = raw.get("sysUpTime", 0)
                e.snmp_sys_name = raw.get("sysName", "")
                e.snmp_sys_services = raw.get("sysServices", 0)

        # mDNS
        if collected.mdns.hostname or collected.mdns.model or collected.mdns.device_type:
            e.mdns = True
            e.mdns_hostname = collected.mdns.hostname
            e.mdns_model = collected.mdns.model
            e.mdns_device_type = collected.mdns.device_type

        # DNS
        if collected.hostname:
            e.dns_hostname = collected.hostname

        return e

    def has_port(self, port: int) -> bool:
        """Проверяет, открыт ли порт."""
        info = self.tcp_ports.get(port, {})
        return info.get("state") == "open"

    def open_ports(self) -> list[int]:
        """Возвращает список открытых портов."""
        return [p for p, info in self.tcp_ports.items() if info.get("state") == "open"]

    def has_open_ports(self) -> bool:
        """Проверяет, есть ли хотя бы один открытый порт."""
        return any(info.get("state") == "open" for info in self.tcp_ports.values())

    def has_ssdp(self) -> bool:
        """Проверяет, ответило ли устройство на SSDP."""
        return self.ssdp_responded

    def has_snmp(self) -> bool:
        """Проверяет, ответило ли устройство на SNMP."""
        return self.snmp_responded
