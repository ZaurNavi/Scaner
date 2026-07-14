#!/usr/bin/env python3
"""
SMB Collector — определение версии ОС через SMB Negotiation (порт 445).
"""

from __future__ import annotations

import socket
import time
from dataclasses import asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import Fingerprint
from models import Device

from .base import ActiveCollector, FingerprintResult
from storage.active_cache import get as cache_get, set as cache_set


class SMBCollector(ActiveCollector):
    PRIORITY = 52
    RELIABILITY = 85

    def __init__(self):
        super().__init__(timeout=1.0)
        self.workers = 64
        self.port = 445
        # Minimal SMB2 Negotiate Protocol Request
        self.smb2_probe = bytes.fromhex(
            "00000048"  # NetBIOS Session Service (Length: 72)
            "fef5424d"  # SMB2 Protocol ID
            "4000"      # StructureSize
            "0000"      # CreditCharge
            "00000000"  # ChannelSequence, Reserved
            "0000"      # Command: Negotiate (0)
            "0000"      # CreditRequest
            "00000000"  # Flags
            "00000000"  # NextCommand
            "0000000000000000"  # MessageId
            "00000000"  # Reserved
            "00000000"  # TreeId
            "00000000000000000000000000000000"  # SessionId
            "00000000000000000000000000000000"  # Signature
            "00000000"  # Reserved
            "0000"      # StructureSize (Negotiate)
            "1000"      # DialectCount (1)
            "0000"      # SecurityMode
            "0000"      # Reserved
            "00000000"  # Capabilities
            "0000000000000000"  # ClientGuid
            "00000000"  # NegotiateContextOffset
            "0000"      # NegotiateContextCount
            "0000"      # Reserved2
            "1002"      # Dialects: SMB 2.1
        )

    def collect(self, device: Device) -> FingerprintResult:
        start_time = time.time()

        cached = cache_get(device.ip, "smb")
        if cached:
            return FingerprintResult(**cached, source="smb", elapsed_ms=0.0)

        if not self.is_available(device):
            return FingerprintResult(
                source="smb",
                raw_data={"responded": False, "reason": "device_unavailable"},
                elapsed_ms=(time.time() - start_time) * 1000,
            )

        smb_data = self._get_smb_info(device.ip)
        elapsed_ms = (time.time() - start_time) * 1000

        if smb_data:
            result = FingerprintResult(source="smb", raw_data=smb_data, elapsed_ms=elapsed_ms)
        else:
            result = FingerprintResult(
                source="smb",
                raw_data={"responded": False, "reason": "no_smb_response"},
                elapsed_ms=elapsed_ms,
            )

        cache_set(device.ip, "smb", asdict(result))
        return result

    def _get_smb_info(self, ip: str) -> dict | None:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((ip, self.port))
            sock.send(self.smb2_probe)
            response = sock.recv(256)
            sock.close()

            if len(response) >= 64 and response[4:8] == b'\xfe\x53\x4d\x42':
                return {"responded": True, "protocol": "SMB2/3", "os_version": "Windows/Samba (SMB2+)"}
            elif len(response) > 0:
                return {"responded": True, "protocol": "SMB1/Unknown", "raw_hex": response[:32].hex()}
            return None

        except (socket.timeout, socket.error, ConnectionResetError):
            return None
        except Exception:
            return None

    def scan(self, devices: list[Device], context: dict | None = None, **kwargs) -> dict[str, FingerprintResult]:
        results: dict[str, FingerprintResult] = {}
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(self.collect, device): device.ip for device in devices}
            for future in as_completed(futures):
                ip = futures[future]
                try:
                    results[ip] = future.result()
                except Exception:
                    results[ip] = FingerprintResult(source="smb", elapsed_ms=0.0)
        return results
