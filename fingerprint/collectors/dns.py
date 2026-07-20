#!/usr/bin/env python3
"""
Reverse DNS коллектор.
v1.7.1a: Интеграция с Configuration Layer.
"""

from __future__ import annotations
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from configuration import get_config_manager


def _resolve_single(ip: str) -> tuple[str, str]:
    try:
        hostname, _, _ = socket.gethostbyaddr(ip)
        return ip, hostname
    except (socket.herror, socket.gaierror, OSError):
        return ip, ""


def collect_hostnames(ips: list[str]) -> dict[str, str]:
    if not ips:
        return {}

    result = {}
    config = get_config_manager()
    workers = min(config.get("collector.dns.workers", 32), len(ips))

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(_resolve_single, ip): ip for ip in ips}
        for future in as_completed(futures):
            ip, hostname = future.result()
            result[ip] = hostname

    return result
