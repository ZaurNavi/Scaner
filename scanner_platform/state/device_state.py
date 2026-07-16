#!/usr/bin/env python3
from enum import Enum

class DeviceState(Enum):
    CONNECTED = "connected"; ROAMING = "roaming"; IDLE = "idle"
    DISCONNECTED = "disconnected"; UNSTABLE = "unstable"
