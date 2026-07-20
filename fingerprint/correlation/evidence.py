#!/usr/bin/env python3
"""
Evidence — факты об устройстве, собранные из UnifiedObservationBatch.
ES-1.8.3: Полная миграция с CollectedData на UnifiedObservationBatch.
"""

from __future__ import annotations
from dataclasses import dataclass, field

from models import Device
from fingerprint import UnifiedObservationBatch


@dataclass
class Evidence:
    """
    Сырые факты об устройстве, извлечённые из Batch.
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
    def from_device(cls, device: Device, batch: UnifiedObservationBatch) -> Evidence:
        """
        ES-1.8.3: Создаёт Evidence из Device и UnifiedObservationBatch.
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

        # Helper для извлечения значения из batch
        def get_val(collector_id: str, attribute: str):
            obs = batch.by_collector(collector_id).by_attribute(attribute).filter(
                lambda o: o.metadata.ip == device.ip
            ).first()
            return obs.normalized_value if obs else None

        # TTL
        ttl_val = get_val("ttl", "ttl")
        if ttl_val is not None:
            e.ping = True
            e.ttl = ttl_val

        # TCP
        tcp_ports = get_val("tcp", "open_ports")
        if tcp_ports is not None and isinstance(tcp_ports, list):
            e.tcp_ports = {str(p): {"state": "open"} for p in tcp_ports}

        # HTTP
        http_services = get_val("http", "http_services")
        if http_services and isinstance(http_services, dict):
            for port, data in http_services.items():
                if isinstance(data, dict):
                    e.http_server = data.get("server", "") or e.http_server
                    e.http_title = data.get("title", "") or e.http_title

        # SSDP/UPnP
        ssdp_info = get_val("ssdp", "ssdp_info")
        if ssdp_info and isinstance(ssdp_info, dict):
            e.ssdp_responded = ssdp_info.get("responded", False)
            if e.ssdp_responded:
                e.ssdp_server = ssdp_info.get("server", "")
                e.ssdp_location = ssdp_info.get("location", "")
                e.ssdp_st = ssdp_info.get("st", "")
                e.ssdp_usn = ssdp_info.get("usn", "")
                e.ssdp_manufacturer = ssdp_info.get("manufacturer", "")
                e.ssdp_model_name = ssdp_info.get("model_name", "")
                e.ssdp_friendly_name = ssdp_info.get("friendly_name", "")
                e.ssdp_model_number = ssdp_info.get("model_number", "")
                e.ssdp_serial_number = ssdp_info.get("serial_number", "")

        # SNMP
        snmp_info = get_val("snmp", "snmp_info")
        if snmp_info and isinstance(snmp_info, dict):
            e.snmp_responded = snmp_info.get("responded", False)
            if e.snmp_responded:
                e.snmp_community = snmp_info.get("community", "")
                e.snmp_sys_descr = snmp_info.get("sysDescr", "")
                e.snmp_sys_object_id = snmp_info.get("sysObjectID", "")
                e.snmp_sys_up_time = snmp_info.get("sysUpTime", 0)
                e.snmp_sys_name = snmp_info.get("sysName", "")
                e.snmp_sys_services = snmp_info.get("sysServices", 0)

        # mDNS
        mdns_hostname = get_val("mdns", "hostname")
        mdns_model = get_val("mdns", "model")
        mdns_device_type = get_val("mdns", "device_type")
        if mdns_hostname or mdns_model or mdns_device_type:
            e.mdns = True
            e.mdns_hostname = mdns_hostname or ""
            e.mdns_model = mdns_model or ""
            e.mdns_device_type = mdns_device_type or ""

        # DNS
        dns_hostname = get_val("dns", "hostname")
        if dns_hostname:
            e.dns_hostname = dns_hostname

        return e

    def has_port(self, port: int) -> bool:
        """Проверяет, открыт ли порт."""
        info = self.tcp_ports.get(str(port), {})
        return info.get("state") == "open"

    def open_ports(self) -> list[int]:
        """Возвращает список открытых портов."""
        return [int(p) for p, info in self.tcp_ports.items() if info.get("state") == "open"]

    def has_open_ports(self) -> bool:
        """Проверяет, есть ли хотя бы один открытый порт."""
        return any(info.get("state") == "open" for info in self.tcp_ports.values())

    def has_ssdp(self) -> bool:
        """Проверяет, ответило ли устройство на SSDP."""
        return self.ssdp_responded

    def has_snmp(self) -> bool:
        """Проверяет, ответило ли устройство на SNMP."""
        return self.snmp_responded
