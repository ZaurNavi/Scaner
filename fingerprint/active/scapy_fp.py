#!/usr/bin/env python3
"""
Scapy Fingerprint Collector — анализ TCP/ICMP стека и топологии.
Включает TCP Options, Window Size, TTL, ICMP Timestamp (Type 13) и Traceroute (TTL 1-3).
"""

from __future__ import annotations

import time
from dataclasses import asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from scapy.all import IP, TCP, ICMP, sr1, conf

from models import Device
from .base import ActiveCollector, FingerprintResult
from storage.active_cache import get as cache_get, set as cache_set

conf.verb = 0


class ScapyFPCollector(ActiveCollector):
    PRIORITY = 35
    RELIABILITY = 95

    def __init__(self):
        super().__init__(timeout=1.0)
        self.workers = 32
        self.port = 80

    def collect(self, device: Device) -> FingerprintResult:
        start_time = time.time()

        cached = cache_get(device.ip, "scapy_fp")
        if cached:
            return FingerprintResult(**cached, source="scapy_fp", elapsed_ms=0.0)

        if not self.is_available(device):
            return FingerprintResult(
                source="scapy_fp",
                raw_data={"responded": False, "reason": "device_unavailable"},
                elapsed_ms=(time.time() - start_time) * 1000,
            )

        fp_data = self._get_fingerprint(device.ip)
        elapsed_ms = (time.time() - start_time) * 1000

        if fp_data:
            result = FingerprintResult(
                source="scapy_fp",
                raw_data=fp_data,
                elapsed_ms=elapsed_ms,
                capabilities=["supports_scapy_fp"]
            )
        else:
            result = FingerprintResult(
                source="scapy_fp",
                raw_data={"responded": False, "reason": "no_response_or_filtered"},
                elapsed_ms=elapsed_ms,
            )

        cache_set(device.ip, "scapy_fp", asdict(result))
        return result

    def _get_fingerprint(self, ip: str) -> dict | None:
        fp_data = {"responded": False}

        # 1. TCP SYN Fingerprint
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
                    if isinstance(opt_val, bytes):
                        tcp_opts[opt_name] = opt_val.hex()
                    else:
                        tcp_opts[opt_name] = opt_val
                fp_data["tcp_options"] = tcp_opts
        except Exception:
            pass

        # 2. ICMP Timestamp Fingerprint (Type 13)
        try:
            icmp_ts_req = IP(dst=ip) / ICMP(type=13, id=12345, seq=1)
            ts_response = sr1(icmp_ts_req, timeout=1.0, retry=0)
            
            if ts_response is not None and ts_response.haslayer(ICMP) and ts_response[ICMP].type == 14:
                fp_data["icmp_timestamp_supported"] = True
        except Exception:
            pass

        # 3. Traceroute TTL (Hops 1, 2, 3)
        # Помогает определить, находится ли устройство за репитером или двойным NAT
        try:
            hops = []
            for ttl in [1, 2, 3]:
                pkt = IP(dst=ip, ttl=ttl) / ICMP(type=8, code=0)
                resp = sr1(pkt, timeout=0.5, retry=0)
                if resp is not None:
                    if resp.haslayer(ICMP) and resp[ICMP].type == 0: # Echo Reply (достигли цели)
                        hops.append({"hop": ttl, "ip": ip, "type": "target"})
                        break
                    elif resp.haslayer(ICMP) and resp[ICMP].type == 11: # Time Exceeded (промежуточный узел)
                        hops.append({"hop": ttl, "ip": resp[IP].src, "type": "intermediate"})
            
            if hops:
                fp_data["traceroute_hops"] = hops
                # Если первый хоп не является целевым IP, значит устройство за NAT/репитером
                if len(hops) > 0 and hops[0]["type"] == "intermediate":
                    fp_data["behind_nat_or_repeater"] = True
        except Exception:
            pass

        return fp_data if fp_data["responded"] or fp_data.get("icmp_timestamp_supported") or fp_data.get("traceroute_hops") else None

    def scan(self, devices: list[Device], context: dict | None = None, **kwargs) -> dict[str, FingerprintResult]:
        results: dict[str, FingerprintResult] = {}
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(self.collect, d): d.ip for d in devices}
            for future in as_completed(futures):
                ip = futures[future]
                try:
                    results[ip] = future.result()
                except Exception:
                    results[ip] = FingerprintResult(source="scapy_fp", elapsed_ms=0.0)
        return results
