#!/usr/bin/env python3
"""
HTTP Collector — получение HTTP-заголовков и контента.
ES-1.8.3: Возвращает строго List[Observation] через ObservationFactory.
"""
from __future__ import annotations

import re
import ssl
import urllib.error
import urllib.request
from models import Device
from .base import ActiveCollector
from configuration import ConfigurationManager
from ..normalization import ObservationFactory


# v1.7.1: Экспортируемые константы для обратной совместимости
HTTP_PORTS = (80, 81, 443, 8080, 8081, 8443)
HTTPS_PORTS = (443, 8443)


class HTTPCollector(ActiveCollector):
    PRIORITY = 70
    RELIABILITY = 90

    def __init__(self, configuration: ConfigurationManager):
        super().__init__(configuration)
        self.timeout = self.config.get("collector.http.timeout", 2.0)
        self.max_body = self.config.get("collector.http.max_body_size", 8192)
        self.http_ports = HTTP_PORTS
        self.https_ports = HTTPS_PORTS

    def collect(self, device: Device) -> list:
        """ES-1.8.3: Возвращает только List[Observation]."""
        if not self.is_available(device):
            return []

        # Определяем открытые порты из контекста (TCP)
        context = getattr(self, "_context", {})
        tcp_res = context.get("tcp", {}).get(device.ip)
        open_ports = set(tcp_res.ports) if tcp_res else set()
        target_ports = [(p, p in self.https_ports) for p in self.http_ports if p in open_ports]

        if not target_ports:
            return []

        services = {}
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

        # Возвращаем Observation с dict (разрешён в NormalizedValue)
        return [ObservationFactory.create(
            collector_id=self.source_name,
            protocol="HTTP",
            device_id=device.ip,
            attribute="http_services",
            value=services
        )]

    def scan(self, devices: list[Device], context: dict | None = None, **kwargs) -> list:
        """ES-1.8.3: scan теперь возвращает List[Observation] для всех устройств."""
        self._context = context or {}
        all_observations = []
        for device in devices:
            if self.is_available(device):
                all_observations.extend(self.collect(device))
        return all_observations

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
                except Exception:
                    pass
                break
            except Exception as e:
                res["error"] = str(e)
        return res
