#!/usr/bin/env python3
"""
Switch Port Collector — определение порта на свитче по MAC-адресу.
ES-1.8.3: Возвращает строго List[Observation] через ObservationFactory.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from models import Device
from .base import ActiveCollector
from configuration import ConfigurationManager
from ..normalization import ObservationFactory

from pysnmp.hlapi import (
    SnmpEngine, CommunityData, UdpTransportTarget, ContextData,
    ObjectType, ObjectIdentity, nextCmd, getCmd,
)


class SwitchPortCollector(ActiveCollector):
    PRIORITY = 46
    RELIABILITY = 90

    def __init__(self, configuration: ConfigurationManager):
        super().__init__(configuration)
        self.communities = [c.strip() for c in self.config.get("collector.snmp.communities", "public").split(",")]
        self.port = self.config.get("collector.snmp.port", 161)
        self.retries = self.config.get("collector.snmp.retries", 2)
        self.workers = self.config.get("collector.switch_port.workers", 16)
        self.timeout = self.config.get("collector.switch_port.timeout", 2.0)
        self.snmp_engine = SnmpEngine()

    def collect(self, device: Device) -> list:
        """ES-1.8.3: Возвращает только List[Observation]."""
        if not device.mac:
            return []

        mac_normalized = device.mac.replace(":", "").lower()
        port_info = self._find_port_on_switch(mac_normalized)
        
        if port_info:
            return [ObservationFactory.create(
                collector_id=self.source_name,
                protocol="SNMP",
                device_id=device.ip,
                attribute="switch_port_info",
                value=port_info
            )]
        return []

    def scan(self, devices: list[Device], context: dict | None = None, **kwargs) -> list:
        """ES-1.8.3: scan возвращает List[Observation] для всех устройств."""
        all_observations = []
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(self.collect, d): d.ip for d in devices}
            for future in as_completed(futures):
                try:
                    all_observations.extend(future.result())
                except Exception:
                    pass
        return all_observations

    def _find_port_on_switch(self, mac: str) -> dict | None:
        switch_ip = self.config.get("collector.dhcp_cisco.ip", "")  # Используем тот же IP роутера/свитча
        if not switch_ip:
            return None
        
        for community in self.communities:
            try:
                bridge_port = self._get_bridge_port(switch_ip, community, mac)
                if bridge_port is None:
                    continue
                if_index = self._get_if_index(switch_ip, community, bridge_port)
                if if_index is None:
                    continue
                interface_name = self._get_interface_name(switch_ip, community, if_index) or f"ifIndex-{if_index}"
                return {
                    "responded": True, 
                    "switch_ip": switch_ip, 
                    "mac": mac, 
                    "bridge_port": bridge_port, 
                    "if_index": if_index, 
                    "interface_name": interface_name, 
                    "community": community
                }
            except Exception:
                continue
        return None

    def _get_bridge_port(self, switch_ip: str, community: str, mac: str) -> int | None:
        mac_oid = ".".join(str(int(x, 16)) for x in [mac[i:i+2] for i in range(0, 12, 2)])
        oid = f"1.3.6.1.2.1.17.4.3.1.2.{mac_oid}"
        try:
            error_indication, error_status, error_index, var_binds = next(getCmd(
                self.snmp_engine, 
                CommunityData(community, mpModel=1), 
                UdpTransportTarget((switch_ip, self.port), timeout=self.timeout, retries=self.retries), 
                ContextData(), 
                ObjectType(ObjectIdentity(oid))
            ))
            if not error_indication and not error_status:
                for var_bind in var_binds:
                    return int(var_bind[1])
        except Exception:
            pass
        return None

    def _get_if_index(self, switch_ip: str, community: str, bridge_port: int) -> int | None:
        oid = f"1.3.6.1.2.1.17.1.4.1.2.{bridge_port}"
        try:
            error_indication, error_status, error_index, var_binds = next(getCmd(
                self.snmp_engine, 
                CommunityData(community, mpModel=1), 
                UdpTransportTarget((switch_ip, self.port), timeout=self.timeout, retries=self.retries), 
                ContextData(), 
                ObjectType(ObjectIdentity(oid))
            ))
            if not error_indication and not error_status:
                for var_bind in var_binds:
                    return int(var_bind[1])
        except Exception:
            pass
        return None

    def _get_interface_name(self, switch_ip: str, community: str, if_index: int) -> str | None:
        oid = f"1.3.6.1.2.1.2.2.1.2.{if_index}"
        try:
            error_indication, error_status, error_index, var_binds = next(getCmd(
                self.snmp_engine, 
                CommunityData(community, mpModel=1), 
                UdpTransportTarget((switch_ip, self.port), timeout=self.timeout, retries=self.retries), 
                ContextData(), 
                ObjectType(ObjectIdentity(oid))
            ))
            if not error_indication and not error_status:
                for var_bind in var_binds:
                    return str(var_bind[1])
        except Exception:
            pass
        return None
