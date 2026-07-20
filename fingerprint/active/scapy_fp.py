#!/usr/bin/env python3
"""
Scapy Fingerprint Collector.
ES-1.8.3: Возвращает строго List[Observation] через ObservationFactory.
"""
from __future__ import annotations

from scapy.all import IP, TCP, ICMP, sr1, conf
from models import Device
from .base import ActiveCollector
from configuration import ConfigurationManager
from ..normalization import ObservationFactory

conf.verb = 0

class ScapyFPCollector(ActiveCollector):
    PRIORITY = 35
    RELIABILITY = 95

    def __init__(self, configuration: ConfigurationManager):
        super().__init__(configuration)
        self.timeout = self.config.get("collector.scapy_fp.timeout", 1.0)
        self.workers = self.config.get("collector.scapy_fp.workers", 32)
        self.port = self.config.get("collector.scapy_fp.port", 80)

    def collect(self, device: Device) -> list:
        """ES-1.8.3: Возвращает только List[Observation]."""
        if not self.is_available(device):
            return []

        fp_data = self._get_fingerprint(device.ip)
        if fp_data:
            return [ObservationFactory.create(
                collector_id=self.source_name,
                protocol="ScapyFP",
                device_id=device.ip,
                attribute="scapy_fingerprint",
                value=fp_data
            )]
        return []

    def _get_fingerprint(self, ip: str) -> dict | None:
        fp_data = {"responded": False}
        try:
            packet = IP(dst=ip) / TCP(dport=self.port, flags="S", window=29200)
            response = sr1(packet, timeout=self.timeout, retry=0)
            if response is not None and response.haslayer(TCP) and response[TCP].flags == "SA":
                fp_data["responded"] = True
                fp_data["protocol"] = "TCP"
                fp_data["ttl"] = response[IP].ttl
                fp_data["window_size"] = response[TCP].window
                fp_data["ip_id"] = response[IP].id
                fp_data["df_flag"] = bool(response[IP].flags & 0x02)
                tcp_opts = {}
                for opt_name, opt_val in response[TCP].options:
                    tcp_opts[opt_name] = opt_val.hex() if isinstance(opt_val, bytes) else opt_val
                fp_data["tcp_options"] = tcp_opts
        except Exception:
            pass

        try:
            icmp_ts_req = IP(dst=ip) / ICMP(type=13, id=12345, seq=1)
            ts_response = sr1(icmp_ts_req, timeout=1.0, retry=0)
            if ts_response is not None and ts_response.haslayer(ICMP) and ts_response[ICMP].type == 14:
                fp_data["icmp_timestamp_supported"] = True
        except Exception:
            pass

        try:
            hops = []
            for ttl in [1, 2, 3]:
                pkt = IP(dst=ip, ttl=ttl) / ICMP(type=8, code=0)
                resp = sr1(pkt, timeout=0.5, retry=0)
                if resp is not None:
                    if resp.haslayer(ICMP) and resp[ICMP].type == 0:
                        hops.append({"hop": ttl, "ip": ip, "type": "target"})
                        break
                    elif resp.haslayer(ICMP) and resp[ICMP].type == 11:
                        hops.append({"hop": ttl, "ip": resp[IP].src, "type": "intermediate"})
            if hops:
                fp_data["traceroute_hops"] = hops
                if len(hops) > 0 and hops[0]["type"] == "intermediate":
                    fp_data["behind_nat_or_repeater"] = True
        except Exception:
            pass

        return fp_data if fp_data["responded"] or fp_data.get("icmp_timestamp_supported") or fp_data.get("traceroute_hops") else None
