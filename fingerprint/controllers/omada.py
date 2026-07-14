#!/usr/bin/env python3
"""
Omada Controller Collector.
Получает данные напрямую от TP-Link Omada Controller через OpenAPI v1.
"""

from __future__ import annotations

import time
import urllib3
import requests
from typing import Any, Dict, List

from config import Omada
from .base import BaseControllerCollector

# Отключаем предупреждения о самоподписанных сертификатах
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class OmadaCollector(BaseControllerCollector):
    def __init__(self):
        self._token: str | None = None
        self._cache: Dict[str, Any] | None = None
        self._cache_timestamp: float = 0.0

    @property
    def name(self) -> str:
        return "omada"

    def is_enabled(self) -> bool:
        return Omada.ENABLED and bool(Omada.CLIENT_ID and Omada.CLIENT_SECRET and Omada.OMADA_ID)

    def collect(self) -> Dict[str, Any]:
        """Основной метод сбора данных с кэшированием."""
        current_time = time.time()
        if self._cache is not None and (current_time - self._cache_timestamp) < Omada.CACHE_TTL:
            return self._cache

        print("\n      [OMADA] Connecting Omada...")
        
        if not self._authenticate():
            print("      [OMADA] ❌ Authentication failed")
            return {"error": "Authentication failed"}

        print("      [OMADA] ✅ Authenticating... OK")
        print("      [OMADA] Loading Sites...")
        sites = self._get_sites()
        if not sites:
            print("      [OMADA] ⚠️ No sites found or Site unavailable")
            return {"sites": [], "clients": [], "devices": []}

        print(f"      [OMADA] ✅ Loading Sites... Found {len(sites)} site(s)")
        
        all_clients = []
        all_devices = []

        for site in sites:
            site_id = site.get("siteId")
            site_name = site.get("name", "Unknown")
            print(f"      [OMADA] Loading Clients & Devices for site: {site_name} ({site_id})...")
            
            clients = self._get_clients(site_id)
            devices = self._get_devices(site_id)
            
            # Добавляем метку сайта к каждому элементу для удобства будущей аналитики
            for c in clients:
                c["_omada_site_name"] = site_name
                c["_omada_site_id"] = site_id
            for d in devices:
                d["_omada_site_name"] = site_name
                d["_omada_site_id"] = site_id

            all_clients.extend(clients)
            all_devices.extend(devices)

        print("      [OMADA] ✅ Done.")

        result = {
            "sites": sites,
            "clients": all_clients,
            "devices": all_devices,
            "timestamp": current_time
        }

        self._cache = result
        self._cache_timestamp = current_time
        return result

    def _authenticate(self) -> bool:
        """Получает access_token через client_credentials."""
        url = f"{Omada.URL}/openapi/authorize/token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": Omada.CLIENT_ID,
            "client_secret": Omada.CLIENT_SECRET,
            "omadacId": Omada.OMADA_ID
        }
        headers = {"Content-Type": "application/json"}
        
        try:
            response = requests.post(url, json=payload, headers=headers, verify=Omada.VERIFY_SSL, timeout=Omada.TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            if data.get("errorCode") == 0 and "result" in data and "access_token" in data["result"]:
                self._token = data["result"]["access_token"]
                return True
            else:
                print(f"      [OMADA] Auth API error: {data}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"      [OMADA] Cannot connect: {e}")
            return False

    def _get_sites(self) -> List[Dict[str, Any]]:
        """Получает список сайтов."""
        url = f"{Omada.URL}/openapi/v1/{Omada.OMADA_ID}/sites"
        return self._make_request(url).get("result", [])

    def _get_clients(self, site_id: str) -> List[Dict[str, Any]]:
        """Получает всех клиентов сайта. Сохраняет ВСЕ поля, которые возвращает API."""
        url = f"{Omada.URL}/openapi/v1/{Omada.OMADA_ID}/sites/{site_id}/clients"
        params = {"page": 1, "pageSize": 500}
        data = self._make_request(url, params)
        # Omada API возвращает список клиентов в data.get("result", [])
        return data.get("result", [])

    def _get_devices(self, site_id: str) -> List[Dict[str, Any]]:
        """Получает все устройства сайта (AP, Switch, Gateway). Сохраняет ВСЕ поля."""
        url = f"{Omada.URL}/openapi/v1/{Omada.OMADA_ID}/sites/{site_id}/devices"
        params = {"page": 1, "pageSize": 500}
        data = self._make_request(url, params)
        return data.get("result", [])

    def _make_request(self, url: str, params: dict | None = None) -> Dict[str, Any]:
        """Универсальный метод для GET-запросов с токеном."""
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json"
        }
        try:
            response = requests.get(url, headers=headers, params=params, verify=Omada.VERIFY_SSL, timeout=Omada.TIMEOUT)
            response.raise_for_status()
            data = response.json()
            if data.get("errorCode") != 0:
                print(f"      [OMADA] API Error on {url}: {data.get('msg', 'Unknown error')}")
                return {"result": []}
            return data
        except requests.exceptions.Timeout:
            print(f"      [OMADA] Timeout on {url}")
            return {"result": []}
        except requests.exceptions.RequestException as e:
            print(f"      [OMADA] Request failed on {url}: {e}")
            return {"result": []}
