#!/usr/bin/env python3
"""
Helper для ping.
Используется TTL, TCP Scanner, HTTP, SSDP и т.д.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass


@dataclass
class PingResult:
    """
    Результат ping-запроса.
    """

    alive: bool = False
    ttl: int | None = None
    latency_ms: float | None = None
    exit_code: int | None = None
    command: str = ""


def ping(ip: str, timeout: float = 1.0, count: int = 1) -> PingResult:
    """
    Выполняет ping и возвращает TTL, latency и alive-статус.
    """

    result = PingResult()

    cmd = [
        "ping", "-c", str(count),
        "-W", str(int(timeout)),
        ip,
    ]

    result.command = " ".join(cmd)

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout + 1,
        )

        result.exit_code = proc.returncode
        output = proc.stdout + proc.stderr

        if proc.returncode == 0:
            result.alive = True

            ttl_match = re.search(r'[Tt][Tt][Ll]=(\d+)', output)
            if ttl_match:
                result.ttl = int(ttl_match.group(1))

            time_match = re.search(r'time=(\d+\.?\d*)', output)
            if time_match:
                result.latency_ms = float(time_match.group(1))

    except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError):
        pass

    return result
