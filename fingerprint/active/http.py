#!/usr/bin/env python3
"""
HTTP Collector.
v1.7.1: Интеграция с Configuration Layer.
"""

from __future__ import annotations

import re
import ssl
import time
import urllib.error
import urllib.request
from dataclasses import asdict

from models import Device
from .base import ActiveCollector, FingerprintResult
from storage.active_cache import get as cache_get, set as cache_set
from configuration import ConfigurationManager


class HTTPCollector(ActiveCollector):
    PRIORITY = 70
    RELIABILITY = 90

    def __init__(self, configuration: ConfigurationManager):
        super().__init__(configuration)
        self.timeout = self.config.get("collector.http.timeout", 2.0)
        self.max_body = self.config.get("collector.http.max_body_size", 8192)
        self.http_ports = [80, 81, 8080, 8081]
        self.https_ports = [443, 8443]

    def collect(self, device: Device) -> FingerprintResult:
        start = time.time()
        cached = cache_get(device.ip, "http")
        if cached:
            return FingerprintResult(**cached, source="http", elapsed_ms=0.0)

        services = {}
        context = getattr(self, "_context", {})
        tcp_res = context.get("tcp", {}).get(device.ip)
        open_ports = set(tcp_res.ports) if tcp_res else set()
        target_ports = [(p, p in self.https_ports) for p in (self.http_ports + self.https_ports) if p in open_ports]

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

        elapsed = (time.time() - start) * 1000
        result = FingerprintResult(source="http", services=services, elapsed_ms=elapsed, raw_data={"ports_checked": [p for p, _ in target_ports]})
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
                if m: res["title"] = m.group(1).strip()
                if resp.headers.get("Location"): res["redirect"] = resp.headers["Location"]
                break
            except urllib.error.HTTPError as e:
                res["status_code"] = e.code
                res["server"] = e.headers.get("Server", "")
                res["content_type"] = e.headers.get("Content-Type", "")
                try: res["body"] = e.read(self.max_body).decode("utf-8", errors="ignore")
                except: pass
                break
            except Exception as e:
                res["error"] = str(e)
        return res
