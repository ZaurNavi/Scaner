#!/usr/bin/env python3
"""
Модели данных для Session Engine (v1.5.3 Full).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any


class SessionStatus(Enum):
    ACTIVE = "ACTIVE"
    ENDED = "ENDED"


class SessionEndReason(Enum):
    TIMEOUT = "TIMEOUT"
    PROGRAM_SHUTDOWN = "PROGRAM_SHUTDOWN"
    MANUAL = "MANUAL"
    RECOVERED = "RECOVERED"
    UNKNOWN = "UNKNOWN"


class SessionQuality(Enum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    RECOVERED = "RECOVERED"


@dataclass
class SessionTimelineEntry:
    timestamp: datetime
    event_type: str
    description: str
    details: Optional[str] = None


@dataclass
class Session:
    # =========================================================================
    # 1. Поля БЕЗ значений по умолчанию (ОБЯЗАНЫ идти первыми!)
    # =========================================================================
    id: str
    device_id: str
    start_time: datetime
    last_seen: datetime
    
    # =========================================================================
    # 2. Поля СО значениями по умолчанию (ОБЯЗАНЫ идти после)
    # =========================================================================
    schema_version: int = 2
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    
    status: SessionStatus = SessionStatus.ACTIVE
    end_reason: Optional[SessionEndReason] = None
    quality: SessionQuality = SessionQuality.PARTIAL
    
    snapshots_count: int = 0
    observations_count: int = 0
    
    ip_history: List[str] = field(default_factory=list)
    hostname_history: List[str] = field(default_factory=list)
    ap_history: List[str] = field(default_factory=list)
    rssi_history: List[int] = field(default_factory=list)
    
    total_bytes_in: int = 0
    total_bytes_out: int = 0
    total_packets_in: int = 0
    total_packets_out: int = 0
    total_flows: int = 0
    traffic_samples_count: int = 0
    
    peak_speed_bps: float = 0.0
    avg_speed_bps: float = 0.0
    active_time_seconds: float = 0.0
    idle_time_seconds: float = 0.0
    
    timeline: List[SessionTimelineEntry] = field(default_factory=list)
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "quality": self.quality.value,
            "snapshots_count": self.snapshots_count,
            "observations_count": self.observations_count,
            "ip_history": self.ip_history,
            "hostname_history": self.hostname_history,
            "ap_history": self.ap_history,
            "rssi_history": self.rssi_history,
            "traffic": {
                "total_bytes_in": self.total_bytes_in,
                "total_bytes_out": self.total_bytes_out,
                "total_packets_in": self.total_packets_in,
                "total_packets_out": self.total_packets_out,
                "total_flows": self.total_flows,
                "samples": self.traffic_samples_count,
                "peak_speed_bps": self.peak_speed_bps,
                "avg_speed_bps": self.avg_speed_bps,
            },
            "timeline": [
                {
                    "timestamp": e.timestamp.isoformat(),
                    "event_type": e.event_type,
                    "description": e.description,
                    "details": e.details
                } for e in self.timeline
            ]
        }
