#!/usr/bin/env python3
"""
SMB Collector — определение версии ОС через SMB Negotiation (порт 445).
ES-1.8.3: Возвращает строго List[Observation] через ObservationFactory.
"""
from __future__ import annotations

import socket
from models import Device
from .base import ActiveCollector
from configuration import ConfigurationManager
from ..normalization import ObservationFactory


class SMBCollector(ActiveCollector):
    PRIORITY = 52
    RELIABILITY = 85

    def __init__(self, configuration: ConfigurationManager):
        super().__init__(configuration)
        self.timeout = self.config.get("collector.smb.timeout", 1.0)
        self.port = self.config.get("collector.smb.port", 445)
        
        # Полный оригинальный SMB2 Negotiate Protocol Request
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

    def collect(self, device: Device) -> list:
        """ES-1.8.3: Возвращает только List[Observation]."""
        if not self.is_available(device):
            return []

        smb_data = self._get_smb_info(device.ip)
        if smb_data:
            return [ObservationFactory.create(
                collector_id=self.source_name,
                protocol="SMB",
                device_id=device.ip,
                attribute="os_version",
                value=smb_data  # Dict разрешён в NormalizedValue
            )]
        return []

    def _get_smb_info(self, ip: str) -> dict | None:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((ip, self.port))
            sock.send(self.smb2_probe)
            response = sock.recv(256)
            sock.close()

            if len(response) >= 64 and response[4:8] == b'\xfe\x53\x4d\x42':
                return {"protocol": "SMB2/3", "os_version": "Windows/Samba (SMB2+)"}
            elif len(response) > 0:
                return {"protocol": "SMB1/Unknown", "raw_hex": response[:32].hex()}
            return None
        except (socket.timeout, socket.error, ConnectionResetError):
            return None
        except Exception:
            return None
