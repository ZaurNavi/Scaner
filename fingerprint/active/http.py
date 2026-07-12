#!/usr/bin/env python3
"""
HTTP Collector — получение HTTP-заголовков и контента.

Архитектура:
- Только собирает сырые данные (server, title, headers, body)
- НЕ определяет vendor/model/device_type — это делает Correlation Engine
"""

from __future__ import annotations

import re
import ssl
import time
import urllib.error
import urllib.request
from dataclasses import asdict

from config import Fingerprint
from models import Device

from .base import ActiveCollector, FingerprintResult
from storage.active_cache import get as cache_get, set as cache_set

# HTTP-порты для проверки
HTTP_PORTS = (80, 81, 443, 8080, 8081, 8443)

# SSL-порты
HTTPS_PORTS = (443, 8443)


class HTTPCollector(ActiveCollector):
    """
    Получает HTTP-баннеры для устройств с открытыми HTTP-портами.
    НЕ интерпретирует данные — только собирает факты.
    """

    PRIORITY = 70
    RELIABILITY = 90

    def __init__(self):
        super().__init__(timeout=Fingerprint.HTTP_TIMEOUT)
        self.max_body = Fingerprint.HTTP_MAX_BODY_SIZE

    def collect(self, device: Device) -> FingerprintResult:
        start = time.time()
        
        # Кэш
        cached = cache_get(device.ip, "http")
        if cached:
            return FingerprintResult(**cached, source="http", elapsed_ms=0.0)

        services = {}

        # Определяем порты из контекста (TCP)
        context = getattr(self, "_context", {})
        tcp_res = context.get("tcp", {}).get(device.ip)
        open_ports = set(tcp_res.ports) if tcp_res else set()
        target_ports = [(p, p in HTTPS_PORTS) for p in HTTP_PORTS if p in open_ports]

        if not target_ports:
            elapsed = (time.time() - start) * 1000
            return FingerprintResult(source="http", elapsed_ms=elapsed)

        for port, is_https in target_ports:
            data = self._fetch_port(device.ip, port, is_https)
            services[port] = {
                "state": "open" if data["status_code"] > 0 else "closed",
                "status_code": data["status_code"],
                "server": data["server"],
                "title": data["title"],
                "content_type": data["content_type"],
                "redirect": data["redirect"],
            }
            if Fingerprint.DEBUG_LEVEL >= 3:
                services[port]["headers"] = data.get("headers", {})

        elapsed = (time.time() - start) * 1000
        
        # Возвращаем ТОЛЬКО сырые данные — без vendor, model, device_type, os, confidence
        result = FingerprintResult(
            source="http",
            services=services,
            elapsed_ms=elapsed,
            raw_data={"ports_checked": [p for p, _ in target_ports]},
        )
        
        # Сохранение в кэш
        cache_set(device.ip, "http", asdict(result))
        
        return result

    def scan(self, devices: list[Device], context: dict | None = None, **kwargs) -> dict[str, FingerprintResult]:
        self._context = context or {}
        return super().scan(devices, context=context, **kwargs)

    def _fetch_port(self, ip: str, port: int, is_https: bool) -> dict:
        scheme = "https" if is_https else "http"
        url = f"{scheme}://{ip}:{port}/"
        res = {"status_code": 0, "server": "", "title": "", "content_type": "", "redirect": "", "headers": {}, "body": "", "error": ""}
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        for method in ["HEAD", "GET"]:
            try:
                req = urllib.request.Request(url, method=method)
                req.add_header("User-Agent", "RepeaterMonitor/1.0")
                resp = urllib.request.urlopen(req, timeout=self.timeout, context=ctx)
                res["status_code"] = resp.status
                res["headers"] = dict(resp.headers)
                res["server"] = resp.headers.get("Server", "")
                res["content_type"] = resp.headers.get("Content-Type", "")
                body = resp.read(self.max_body).decode("utf-8", errors="ignore")
                res["body"] = body
                m = re.search(r"<title[^>]*>([^<]+)</title>", body, re.I | re.S)
                if m:
                    res["title"] = m.group(1).strip()
                if resp.headers.get("Location"):
                    res["redirect"] = resp.headers["Location"]
                break
            except urllib.error.HTTPError as e:
                res["status_code"] = e.code
                res["server"] = e.headers.get("Server", "")
                res["content_type"] = e.headers.get("Content-Type", "")
                try:
                    res["body"] = e.read(self.max_body).decode("utf-8", errors="ignore")
                except:
                    pass
                break
            except Exception as e:
                res["error"] = str(e)
        return res
