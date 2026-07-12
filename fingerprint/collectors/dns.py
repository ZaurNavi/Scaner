"""
Reverse DNS коллектор.
"""

from __future__ import annotations

import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import Fingerprint


def _resolve_single(ip: str) -> tuple[str, str]:
    """
    Резолвит один IP через reverse DNS.
    Возвращает (ip, hostname).
    """

    try:
        hostname, _, _ = socket.gethostbyaddr(ip)
        return ip, hostname
    except (socket.herror, socket.gaierror, OSError):
        return ip, ""


def collect_hostnames(ips: list[str]) -> dict[str, str]:
    """
    Получает hostname через reverse DNS для всех IP.
    Использует ThreadPoolExecutor для параллельных запросов.
    Возвращает {ip: hostname}.
    """

    if not ips:
        return {}

    result = {}

    workers = min(Fingerprint.DNS_WORKERS, len(ips))

    with ThreadPoolExecutor(max_workers=workers) as executor:

        futures = {
            executor.submit(_resolve_single, ip): ip
            for ip in ips
        }

        for future in as_completed(futures):
            ip, hostname = future.result()
            result[ip] = hostname

    return result
