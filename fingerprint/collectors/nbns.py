"""
NBNS Passive Collector Module (ES-1.8.5).
Strictly follows the layered architecture: Collector -> Policy -> Adapter -> Wrappers -> Impacket.
"""

import socket
import logging
import time
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass

# Проверка наличия impacket
try:
    from impacket.nmb import NBNSPacket, NetBIOSTimeout, NetBIOSError
    IMPACKET_AVAILABLE = True
except ImportError:
    IMPACKET_AVAILABLE = False
    NBNSPacket = None
    class NetBIOSTimeout(Exception): pass
    class NetBIOSError(Exception): pass

# Абсолютные импорты для гарантии работы вне зависимости от точки входа
from fingerprint.collectors.base import BasePassiveCollector
from fingerprint.collectors.registry import passive_collector
from fingerprint.normalization.models import Observation, ObservationMetadata
from fingerprint.normalization.factory import ObservationFactory
from configuration.manager import ConfigurationManager

logger = logging.getLogger(__name__)

# Constants
NBNS_PORT = 137
OPCODE_QUERY = 0x0
OPCODE_REGISTRATION = 0x5
OPCODE_RELEASE = 0x6
RR_TYPE_NBSTAT = 0x21

# Ignored Group Suffixes (RFC1002)
IGNORED_GROUP_SUFFIXES = {
    0x1B,  # Domain Master Browser
    0x1C,  # Domain Controllers
    0x1D,  # Local Master Browser
    0x1E,  # Browser Service Elections
    0x01,  # Master Browser
    0x03,  # Messenger Service
    0x06,  # RAS Server Service
}

# Special Names to Ignore
IGNORED_NAMES = {"WORKGROUP", "MSHOME", "__MSBROWSE__", "MASTER_BROWSER"}

@dataclass(frozen=True)
class NBNSRecord:
    """Immutable raw data extracted from NBNS packet."""
    name: str
    ip: str
    ttl: int
    suffix: int
    opcode: int
    qr: int
    rr_type: int
    source_type: str  # QUERY, ANSWER, NODE_STATUS, REGISTRATION, RELEASE
    confidence_hint: float

class _BaseWrapper:
    """Base wrapper to isolate impacket dependencies."""
    def __init__(self, entry):
        self._entry = entry

    def extract_data(self) -> Dict[str, Any]:
        raise NotImplementedError

    @staticmethod
    def _extract_suffix_from_name(name_str: str) -> int:
        return 0

class _ImpacketAnswerWrapper(_BaseWrapper):
    """Wrapper for Answer Section records."""
    
    def extract_data(self) -> Dict[str, Any]:
        suffix = getattr(self._entry, 'suffix', None)
        
        if suffix is None:
            if hasattr(self._entry, 'entry') and hasattr(self._entry.entry, 'suffix'):
                suffix = self._entry.entry.suffix
            else:
                suffix = self._extract_suffix_from_name(getattr(self._entry, 'name', '')) or 0
        
        return {
            'name': getattr(self._entry, 'name', ''),
            'ip': getattr(self._entry, 'address', '0.0.0.0'),
            'ttl': getattr(self._entry, 'ttl', 0),
            'suffix': suffix,
            'opcode': 0,
            'qr': 1,
            'rr_type': getattr(self._entry, 'type', 0),
        }

class _ImpacketNodeStatusWrapper(_BaseWrapper):
    """Wrapper for Node Status (NBSTAT) records containing Name Table."""
    
    def extract_data(self) -> List[Dict[str, Any]]:
        records = []
        # WARNING: impacket does not expose public API for NBSTAT Name Table.
        # We intentionally access internal fields here.
        name_table = getattr(self._entry, 'nbns_names', [])
        
        if not name_table and hasattr(self._entry, 'entry'):
            name_table = getattr(self._entry.entry, 'name_table', [])

        for entry in name_table:
            name = getattr(entry, 'name', '')
            suffix = getattr(entry, 'suffix', 0)
            
            if not name:
                continue
                
            records.append({
                'name': name,
                'ip': getattr(self._entry, 'address', '0.0.0.0'),
                'ttl': 0,
                'suffix': suffix,
                'opcode': 0,
                'qr': 1,
                'rr_type': RR_TYPE_NBSTAT,
            })
            
        return records

class _ImpacketQuestionWrapper(_BaseWrapper):
    """Wrapper for Question Section records."""
    
    def extract_data(self) -> Dict[str, Any]:
        suffix = getattr(self._entry, 'suffix', None)
        if suffix is None:
             suffix = 0
            
        return {
            'name': getattr(self._entry, 'question_name', ''),
            'ip': '0.0.0.0',
            'ttl': 0,
            'suffix': suffix,
            'opcode': getattr(self._entry, 'opcode', 0),
            'qr': 0,
            'rr_type': getattr(self._entry, 'type', 0),
        }

class _ImpacketNBNSAdapter:
    """Adapter layer: Converts impacket packets to list of NBNSRecord dicts."""
    
    @staticmethod
    def parse(data: bytes, source_ip: str) -> List[NBNSRecord]:
        try:
            packet = NBNSPacket(data)
        except Exception:
            return []

        results = []
        
        def _parse_section(entries, section_type):
            if not entries:
                return
            for entry in entries:
                try:
                    if isinstance(entry, dict):
                        wrapper_data = {'name': entry.get('name', ''), 'suffix': 0, 'ip': entry.get('address', source_ip), 'ttl': 0, 'opcode': 0, 'qr': 1, 'rr_type': entry.get('type', 0)}
                    else:
                        if section_type == 'questions':
                            w = _ImpacketQuestionWrapper(entry)
                        elif section_type == 'answers':
                             if getattr(entry, 'type', 0) == RR_TYPE_NBSTAT:
                                w = _ImpacketNodeStatusWrapper(entry)
                                sub_records = w.extract_data()
                                for rec in sub_records:
                                    rec['source_type'] = 'NODE_STATUS'
                                    rec['confidence_hint'] = 0.95
                                    rec['opcode'] = 0
                                    rec['qr'] = 1
                                    results.append(NBNSRecord(**rec))
                                continue
                             else:
                                w = _ImpacketAnswerWrapper(entry)
                        else:
                            continue

                        wrapper_data = w.extract_data()
                        if isinstance(wrapper_data, list):
                             for rec in wrapper_data:
                                rec['source_type'] = 'NODE_STATUS'
                                rec['confidence_hint'] = 0.95
                                results.append(NBNSRecord(**rec))
                             continue
                    
                    source_type = section_type.upper().rstrip('S')
                    if section_type == 'answers':
                        source_type = 'ANSWER'
                    
                    results.append(NBNSRecord(
                        name=wrapper_data['name'],
                        ip=wrapper_data['ip'] if wrapper_data['ip'] != '0.0.0.0' else source_ip,
                        ttl=wrapper_data['ttl'],
                        suffix=wrapper_data['suffix'],
                        opcode=wrapper_data['opcode'],
                        qr=wrapper_data['qr'],
                        rr_type=wrapper_data['rr_type'],
                        source_type=source_type,
                        confidence_hint=0.5
                    ))
                except Exception:
                    continue

        _parse_section(getattr(packet, 'questions', []), 'questions')
        _parse_section(getattr(packet, 'answers', []), 'answers')
        _parse_section(getattr(packet, 'additionals', []), 'additionals')
        
        opcode = getattr(packet, 'opcode', 0)
        qr = getattr(packet, 'qr', 0)
        
        if opcode == OPCODE_REGISTRATION and qr == 0:
             pass
        elif opcode == OPCODE_RELEASE:
             rel_name = ""
             if packet.questions:
                 rel_name = getattr(packet.questions[0], 'question_name', "UNKNOWN")
             
             results.append(NBNSRecord(
                 name=rel_name,
                 ip=source_ip,
                 ttl=0,
                 suffix=0,
                 opcode=OPCODE_RELEASE,
                 qr=qr,
                 rr_type=0,
                 source_type="RELEASE",
                 confidence_hint=0.90
             ))

        return results

class _NBNSPolicy:
    """Policy Layer: Decides whether to keep a record and calculates final confidence."""
    
    @staticmethod
    def should_keep(record: NBNSRecord) -> bool:
        name = record.name.strip()
        
        if not name:
            return False
            
        if name.upper() in IGNORED_NAMES:
            return False
            
        if record.suffix in IGNORED_GROUP_SUFFIXES:
            return False
            
        if not any(c.isalnum() for c in name):
            return False
            
        return True

    @staticmethod
    def calculate_confidence(record: NBNSRecord) -> float:
        if record.source_type == "NODE_STATUS":
            return 0.95
        if record.source_type == "REGISTRATION":
            return 0.90
        if record.source_type == "ANSWER":
            return 0.85
        if record.source_type == "QUERY":
            return 0.35
        if record.source_type == "RELEASE":
            return 0.90
            
        return 0.5

class NBNSCollector(BasePassiveCollector):
    """
    NBNS Passive Collector.
    Responsibilities: Socket management, coordination.
    Does NOT know: impacket internals, business logic, confidence rules.
    """

    def __init__(self, configuration: ConfigurationManager):
        super().__init__(configuration)
        self._enabled = configuration.get("fingerprint.collectors.nbns.enabled", True)
        self._timeout = configuration.get("fingerprint.collectors.nbns.timeout", 0.5)
        self._learn_queries = configuration.get("fingerprint.collectors.nbns.learn_from_queries", False)

    @property
    def capabilities(self) -> List[str]:
        return ["hostname_discovery", "nbns_resolution"]

    def observe(self, target_ips: List[str], interface: Optional[str] = None, context: Optional[Dict] = None) -> List[Observation]:
        if not self._enabled:
            return []
        if not IMPACKET_AVAILABLE:
            logger.warning('impacket not installed. NBNS Collector disabled.')
            return []

        observations = []
        seen = set()
        sock = None
        
        logger.info("[PASSIVE] NBNS Collector initialized")

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.bind(("0.0.0.0", NBNS_PORT))
            sock.settimeout(self._timeout)
            
            end_time = time.monotonic() + self._timeout
            
            while time.monotonic() < end_time:
                try:
                    data, addr = sock.recvfrom(4096)
                    source_ip = addr[0]
                    packet_timestamp = datetime.now()

                    records = _ImpacketNBNSAdapter.parse(data, source_ip)
                    
                    for rec in records:
                        dedup_key = (rec.ip, rec.name, rec.suffix, rec.source_type)
                        if dedup_key in seen:
                            continue
                        seen.add(dedup_key)
                        
                        if not _NBNSPolicy.should_keep(rec):
                            continue
                            
                        if rec.source_type == "QUERY" and not self._learn_queries:
                            continue
                            
                        if rec.source_type == "RELEASE":
                            logger.debug(f"NBNS RELEASE detected: {rec.name} from {rec.ip}")
                            continue

                        confidence = _NBNSPolicy.calculate_confidence(rec)
                        
                        metadata = ObservationMetadata(
                            ip=rec.ip,
                            timestamp=packet_timestamp,
                            protocol="NBNS",
                            source_ip=source_ip,
                            interface=interface
                        )
                        
                        obs = ObservationFactory.hostname(rec.name, metadata)
                        observations.append(obs)
                        
                        logger.debug(f"NBNS: {rec.name} ({rec.suffix}) from {rec.ip} [{rec.source_type}] (Conf: {confidence})")

                except NetBIOSTimeout:
                    break
                except (NetBIOSError, socket.error) as e:
                    logger.warning(f"NBNS Socket error: {e}")
                    break
                except Exception as e:
                    logger.error(f"Unexpected error in NBNS loop: {e}")
                    break

        except PermissionError:
            logger.warning("Permission denied binding NBNS port 137.")
        except Exception as e:
            logger.error(f"NBNS Collector critical failure: {e}")
        finally:
            if sock:
                sock.close()
                
        return observations

@passive_collector(
    id="nbns",
    name="nbns",
    version="ES-1.8.5",
    priority=40,
    protocol="NBNS",
    capabilities=["hostname_discovery", "nbns_resolution"],
    enabled_by_default=True
)
def get_nbns_collector(configuration: ConfigurationManager) -> NBNSCollector:
    return NBNSCollector(configuration)
