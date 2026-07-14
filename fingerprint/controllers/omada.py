#!/usr/bin/env python3
"""
Omada Controller Collector.
Получает данные напрямую от TP-Link Omada Controller через OpenAPI v1.
Полностью соответствует официальной документации Omada Open API.
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

        print(f"      [OMADA] ✅ Done. Clients: {len(all_clients)}, Devices: {len(all_devices)}")

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
        """
        Получает access_token через client_credentials.
        Согласно документации: grant_type в QUERY, остальные поля в BODY.
        """
        url = f"{Omada.URL}/openapi/authorize/token"
        
        # grant_type передается в QUERY параметрах
        params = {"grant_type": "client_credentials"}
        
        # Остальные поля передаются в BODY
        payload = {
            "omadacId": Omada.OMADA_ID,
            "client_id": Omada.CLIENT_ID,
            "client_secret": Omada.CLIENT_SECRET
        }
        headers = {"Content-Type": "application/json"}
        
        try:
            response = requests.post(
                url, 
                params=params,  # grant_type в query
                json=payload,   # credentials в body
                headers=headers, 
                verify=Omada.VERIFY_SSL, 
                timeout=Omada.TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            
            # Согласно документации, поле называется accessToken (camelCase)
            if data.get("errorCode") == 0 and "result" in data and "accessToken" in data["result"]:
                self._token = data["result"]["accessToken"]
                return True
            else:
                error_code = data.get("errorCode")
                error_msg = data.get("msg", "Unknown error")
                print(f"      [OMADA] Auth API error: {error_msg} (Code: {error_code})")
                return False
        except requests.exceptions.RequestException as e:
            print(f"      [OMADA] Cannot connect: {e}")
            return False

    def _get_sites(self) -> List[Dict[str, Any]]:
        """Получает список сайтов."""
        url = f"{Omada.URL}/openapi/v1/{Omada.OMADA_ID}/sites"
        params = {"page": 1, "pageSize": 50}
        data = self._make_request(url, params)
        # Согласно документации, массив находится в result.data
        return data.get("result", {}).get("data", [])

    def _get_clients(self, site_id: str) -> List[Dict[str, Any]]:
        """
        Получает всех клиентов сайта с учетом пагинации.
        Сохраняет ВСЕ поля, которые возвращает API.
        """
        url = f"{Omada.URL}/openapi/v1/{Omada.OMADA_ID}/sites/{site_id}/clients"
        all_clients = []
        page = 1
        page_size = 500
        
        while True:
            params = {"page": page, "pageSize": page_size}
            data = self._make_request(url, params)
            clients_on_page = data.get("result", {}).get("data", [])
            all_clients.extend(clients_on_page)
            
            # Если получили меньше, чем page_size, значит это последняя страница
            if len(clients_on_page) < page_size:
                break
            page += 1
            
        return all_clients

    def _get_devices(self, site_id: str) -> List[Dict[str, Any]]:
        """
        Получает все устройства сайта (AP, Switch, Gateway) с учетом пагинации.
        Сохраняет ВСЕ поля.
        """
        url = f"{Omada.URL}/openapi/v1/{Omada.OMADA_ID}/sites/{site_id}/devices"
        all_devices = []
        page = 1
        page_size = 500
        
        while True:
            params = {"page": page, "pageSize": page_size}
            data = self._make_request(url, params)
            devices_on_page = data.get("result", {}).get("data", [])
            all_devices.extend(devices_on_page)
            
            if len(devices_on_page) < page_size:
                break
            page += 1
            
        return all_devices

    def _make_request(self, url: str, params: dict | None = None, retry: bool = True) -> Dict[str, Any]:
        """
        Универсальный метод для GET-запросов с токеном.
        Согласно документации: префикс токена в заголовке — 'AccessToken=', а не 'Bearer'.
        Обрабатывает истекший токен (401 или errorCode -44112/-44113) автоматической переавторизацией.
        """
        headers = {
            # КРИТИЧЕСКИ ВАЖНО: Префикс AccessToken=, а не Bearer!
            "Authorization": f"AccessToken={self._token}",
            "Content-Type": "application/json"
        }
        try:
            response = requests.get(
                url, 
                headers=headers, 
                params=params, 
                verify=Omada.VERIFY_SSL, 
                timeout=Omada.TIMEOUT
            )
            
            # Проверяем, не истек ли токен
            is_auth_error = False
            try:
                response_json = response.json()
                error_code = response_json.get("errorCode")
                # Коды ошибок из документации: -44112 (token expired), -44113 (token invalid)
                if error_code in [-44112, -44113]:
                    is_auth_error = True
            except:
                pass
            
            if response.status_code == 401 or is_auth_error:
                if retry:
                    print("      [OMADA] ⚠️ Token expired or invalid. Re-authenticating...")
                    if self._authenticate():
                        # Повторяем запрос с новым токеном (но только один раз, чтобы избежать бесконечного цикла)
                        return self._make_request(url, params, retry=False)
                    else:
                        return {"errorCode": -1, "result": {"data": []}}
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            print(f"      [OMADA] Timeout on {url}")
            return {"errorCode": -1, "result": {"data": []}}
        except requests.exceptions.RequestException as e:
            print(f"      [OMADA] Request failed on {url}: {e}")
            return {"errorCode": -1, "result": {"data": []}}
