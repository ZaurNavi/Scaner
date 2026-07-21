#!/usr/bin/env python3
"""
LLMNR Passive Collector Module.
Implements Link-Local Multicast Name Resolution passive listening.
Complies with ES-1.8.4 Architecture (Passive Only).

ES-1.8.4:
- Только пассивное прослушивание (без probe/query)
- Не определяет HOSTNAME/FQDN (задача Normalizer)
- Использует ObservationFactory.create() с атрибутом "hostname"
- Все параметры из Configuration Layer
- Ошибки логируются как debug/warning, исключения не выбрасываются
"""

from __future__ import annotations

import socket
import struct
import logging
import time
from dataclasses import dataclass
from typing import List, Any, Tuple, Optional

from configuration import ConfigurationManager
from .base import BasePassiveCollector
from .registry import passive_collector
from ..normalization import ObservationFactory

logger = logging.getLogger(__name__)

# Constants
LLMNR_IPV4_MULTICAST = "224.0.0.252"
LLMNR_PORT = 5355

# DNS/LLMNR Types
_QTYPE_A = 1
_QTYPE_AAAA = 28


@dataclass(frozen=True)
class LLMNRRecord:
    """Parsed LLMNR Record."""
    name: str
    record_type: int
    ip_address: Optional[str]


class _LLMNRParser:
    """
    Internal parser for LLMNR packets.
    Isolates binary parsing logic from the Collector (SRP).
    """

    @staticmethod
    def parse(data: bytes, addr: Tuple[str, int]) -> List[LLMNRRecord]:
        """Parse raw UDP packet into LLMNR records."""
        records = []
        if len(data) < 12:
            return records

        try:
            # Header
            (id_val, flags, qdcount, ancount, nscount, arcount) = struct.unpack(">HHHHHH", data[:12])
            
            qr = (flags >> 15) & 0x1
            rcode = flags & 0xF

            # Only process successful responses (QR=1, RCODE=0)
            if qr != 1 or rcode != 0 or ancount == 0:
                return records

            offset = 12
            
            # Skip Question Section
            for _ in range(qdcount):
                if offset >= len(data):
                    break
                # Skip name
                while offset < len(data) and data[offset] != 0:
                    length = data[offset]
                    offset += length + 1
                offset += 1  # Null terminator
                offset += 4  # Type + Class

            # Parse Answer Section
            for _ in range(ancount):
                if offset >= len(data):
                    break
                
                # Parse Name (handle compression pointers simply or read labels)
                name_parts = []
                jumped = False
                
                while offset < len(data):
                    byte = data[offset]
                    if byte == 0:
                        offset += 1
                        break
                    elif (byte & 0xC0) == 0xC0:
                        # Pointer (simplified: just break to avoid infinite loops)
                        offset += 2
                        jumped = True
                        break
                    else:
                        length = byte
                        offset += 1
                        if offset + length > len(data):
                            break
                        name_parts.append(data[offset:offset+length].decode('ascii', errors='ignore'))
                        offset += length
                
                name = ".".join(name_parts) if name_parts else ""
                
                # Read Type, Class, TTL, Length
                if offset + 10 > len(data):
                    break
                    
                rtype, rclass, ttl, rdlength = struct.unpack(">HHIH", data[offset:offset+10])
                offset += 10
                
                if offset + rdlength > len(data):
                    break
                    
                rdata = data[offset:offset+rdlength]
                offset += rdlength
                
                # Extract IP
                ip_addr = None
                if rtype == _QTYPE_A and rdlength == 4:
                    ip_addr = ".".join(str(b) for b in rdata)
                elif rtype == _QTYPE_AAAA and rdlength == 16:
                    # Simple IPv6 formatting
                    ip_addr = ":".join(f"{b:02x}" for b in rdata)
                
                if name and ip_addr:
                    records.append(LLMNRRecord(name=name, record_type=rtype, ip_address=ip_addr))

        except Exception as e:
            logger.debug(f"Failed to parse LLMNR packet from {addr}: {e}")
            
        return records


@passive_collector(
    id="llmnr",
    name="LLMNR Collector",
    version="ES-1.8.4",
    protocol="LLMNR",
    category="passive",
    priority=30,
    enabled_by_default=True,
    capabilities=("hostname_discovery", "llmnr_resolution"),
    default_category="identity"
)
class LLMNRCollector(BasePassiveCollector):
    """
    LLMNR Passive Collector.
    
    Responsibilities:
    - Bind to UDP 5355 multicast.
    - Listen for incoming LLMNR responses.
    - Parse packets via _LLMNRParser.
    - Create Observations via Factory.
    
    Does NOT:
    - Send queries (Active).
    - Decide HOSTNAME vs FQDN (Normalizer's job).
    - Know about other protocols (DNS, mDNS).
    """

    def __init__(self, configuration: ConfigurationManager):
        super().__init__(configuration)
        
        # Configuration Layer access only (no magic numbers)
        self._socket_timeout = configuration.get("fingerprint.collectors.llmnr.timeout", 0.5)
        self._operation_timeout = configuration.get("fingerprint.collectors.llmnr.operation_timeout", 2.0)
        self._workers = configuration.get("fingerprint.collectors.llmnr.workers", 32)
        self._port = configuration.get("fingerprint.collectors.llmnr.port", LLMNR_PORT)
        self._multicast = configuration.get("fingerprint.collectors.llmnr.multicast", True)

    def observe(self, ips: List[str], context: dict[str, Any] = None) -> List:
        """
        Passive observation: Listen only.
        ES-1.8.4: Возвращает List[Observation].
        
        Args:
            ips: Список IP для контекста (в пассивном режиме не используется для таргетинга)
            context: Дополнительный контекст
            
        Returns:
            List[Observation]: Список наблюдений
        """
        if not ips:
            return []

        observations = []
        start_time = time.time()
        
        # Определяем интерфейсы (упрощенно - один поток на все)
        try:
            records = self._listen_all_interfaces()
            
            current_time = time.time()
            for rec in records:
                # Создаем Observation через Factory
                # Collector НЕ решает HOSTNAME/FQDN - передает сырое имя
                obs = ObservationFactory.create(
                    collector_id=self.id,
                    protocol=self.protocol,
                    device_id=rec.ip_address,
                    attribute="hostname",
                    value=rec.name
                )
                observations.append(obs)
                
        except Exception as e:
            # Критическая ошибка - логируем и возвращаем пустой список
            logger.warning(f"LLMNR Collector critical failure: {e}. Returning empty result.")
            return []

        return observations

    def _listen_all_interfaces(self) -> List[LLMNRRecord]:
        """Listen on all available interfaces."""
        all_records = []
        sock = None
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind to all interfaces
            bind_addr = "0.0.0.0"
            sock.bind((bind_addr, self._port))
            
            # Join Multicast
            if self._multicast:
                mreq = socket.inet_aton(LLMNR_IPV4_MULTICAST) + socket.inet_aton(bind_addr)
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            
            sock.settimeout(self._socket_timeout)
            
            end_time = time.time() + self._operation_timeout
            
            while time.time() < end_time:
                try:
                    data, addr = sock.recvfrom(4096)
                    records = _LLMNRParser.parse(data, addr)
                    all_records.extend(records)
                    
                except socket.timeout:
                    continue
                except PermissionError:
                    logger.warning(f"Permission denied binding LLMNR port {self._port}. Requires root/admin?")
                    break
                except OSError as e:
                    logger.debug(f"OS Error on LLMNR socket: {e}")
                    break
                except Exception as e:
                    logger.debug(f"Unexpected error receiving LLMNR: {e}")
                    continue
                    
        except Exception as e:
            logger.debug(f"Failed to setup LLMNR listener: {e}")
        finally:
            if sock:
                try:
                    sock.close()
                except:
                    pass
                    
        return all_records
