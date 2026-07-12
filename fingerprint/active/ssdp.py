#!/usr/bin/env python3
"""
SSDP/UPnP Collector — обнаружение устройств через multicast.

Архитектура:
- Отправляет M-SEARCH на 239.255.255.250:1900
- Собирает ответы от устройств (Smart TV, камеры, принтеры, NAS)
- Парсит HTTP-подобные заголовки (SERVER, LOCATION, ST, USN)
- Опционально делает GET к LOCATION для XML-описания
- Возвращает только сырые данные — интерпретация в Correlation Engine
"""

from __future__ import annotations

import socket
import time
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict

from config import Fingerprint
from models import Device

from .base import ActiveCollector, FingerprintResult
from storage.active_cache import get as cache_get, set as cache_set


# M-SEARCH запрос для обнаружения всех UPnP-устройств
MSEARCH_REQUEST = (
    "M-SEARCH * HTTP/1.1\r\n"
    "HOST: {multicast}:{port}\r\n"
    "MAN: \"ssdp:discover\"\r\n"
    "MX: {mx}\r\n"
    "ST: ssdp:all\r\n"
    "\r\n"
)


class SSDPCollector(ActiveCollector):
    """
    Собирает данные SSDP/UPnP через multicast.
    НЕ интерпретирует данные — только собирает факты.
    """

    PRIORITY = 60
    RELIABILITY = 70

    def __init__(self):
        super().__init__(timeout=Fingerprint.SSDP_TIMEOUT)
        self.multicast = Fingerprint.SSDP_MULTICAST
        self.port = Fingerprint.SSDP_PORT
        self.mx = Fingerprint.SSDP_MX
        self.fetch_description = Fingerprint.SSDP_FETCH_DESCRIPTION
        self.description_timeout = Fingerprint.SSDP_DESCRIPTION_TIMEOUT

    def collect(self, device: Device) -> FingerprintResult:
        """
        SSDP работает через multicast, поэтому collect() не используется.
        Вся логика в scan().
        """
        return FingerprintResult(source="ssdp", elapsed_ms=0.0)

    def scan(self, devices: list[Device], context: dict | None = None, **kwargs) -> dict[str, FingerprintResult]:
        """
        Отправляет M-SEARCH и собирает ответы от всех устройств.
        Возвращает результат для КАЖДОГО устройства (даже если не ответило).
        """
        if not Fingerprint.SSDP_ENABLED:
            # Если SSDP отключён, возвращаем пустые результаты для всех
            return {d.ip: FingerprintResult(source="ssdp", elapsed_ms=0.0) for d in devices}

        start_time = time.time()
        results: dict[str, FingerprintResult] = {}

        # Проверяем кэш для каждого устройства
        for d in devices:
            cached = cache_get(d.ip, "ssdp")
            if cached:
                results[d.ip] = FingerprintResult(**cached, source="ssdp", elapsed_ms=0.0)

        # Устройства без кэша
        uncached_devices = [d for d in devices if d.ip not in results]
        if not uncached_devices:
            return results

        # Отправляем M-SEARCH и собираем ответы
        ssdp_responses = self._send_msearch(uncached_devices)
        scan_elapsed = (time.time() - start_time) * 1000

        # Обрабатываем ответы
        for ip, response_data in ssdp_responses.items():
            # Опционально получаем XML-описание
            if self.fetch_description and response_data.get("location"):
                xml_data = self._fetch_description(response_data["location"])
                response_data.update(xml_data)

            # Создаём FingerprintResult с сырыми данными
            result = FingerprintResult(
                source="ssdp",
                server=response_data.get("server", ""),
                raw_data=response_data,
                elapsed_ms=scan_elapsed,
            )
            results[ip] = result

            # Сохраняем в кэш
            cache_set(ip, "ssdp", asdict(result))

        # ВАЖНО: возвращаем пустые результаты для устройств, которые не ответили
        # Это даёт информацию "SSDP был запущен, но устройство не ответило"
        for d in uncached_devices:
            if d.ip not in results:
                empty_result = FingerprintResult(
                    source="ssdp",
                    raw_data={
                        "responded": False,
                        "reason": "no_ssdp_response",
                    },
                    elapsed_ms=scan_elapsed,
                )
                results[d.ip] = empty_result
                # Сохраняем в кэш
                cache_set(d.ip, "ssdp", asdict(empty_result))

        return results

    def _send_msearch(self, devices: list[Device]) -> dict[str, dict]:
        """
        Отправляет M-SEARCH multicast запрос и собирает ответы.
        Возвращает dict {ip: response_data}.
        """
        responses: dict[str, dict] = {}

        try:
            # Создаём UDP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(self.timeout)

            # Формируем M-SEARCH запрос
            request = MSEARCH_REQUEST.format(
                multicast=self.multicast,
                port=self.port,
                mx=self.mx,
            ).encode("utf-8")

            # Отправляем на multicast адрес
            sock.sendto(request, (self.multicast, self.port))

            # Собираем ответы в течение timeout
            end_time = time.time() + self.timeout
            target_ips = {d.ip for d in devices}

            while time.time() < end_time:
                try:
                    data, addr = sock.recvfrom(4096)
                    ip = addr[0]

                    # Проверяем, что ответ от нашего целевого IP
                    if ip in target_ips and ip not in responses:
                        response_data = self._parse_ssdp_response(data.decode("utf-8", errors="ignore"))
                        response_data["responded"] = True
                        responses[ip] = response_data
                except socket.timeout:
                    break
                except Exception:
                    continue

            sock.close()

        except Exception as e:
            # Если multicast не работает (например, нет прав), просто возвращаем пустой результат
            pass

        return responses

    def _parse_ssdp_response(self, response: str) -> dict:
        """
        Парсит SSDP-ответ (HTTP-подобные заголовки).
        """
        data = {
            "server": "",
            "location": "",
            "st": "",
            "usn": "",
            "cache_control": "",
        }

        for line in response.split("\r\n"):
            if ":" in line:
                key, _, value = line.partition(":")
                key = key.strip().upper()
                value = value.strip()

                if key == "SERVER":
                    data["server"] = value
                elif key == "LOCATION":
                    data["location"] = value
                elif key == "ST":
                    data["st"] = value
                elif key == "USN":
                    data["usn"] = value
                elif key == "CACHE-CONTROL":
                    data["cache_control"] = value

        return data

    def _fetch_description(self, location: str) -> dict:
        """
        Делает GET к LOCATION для получения XML-описания устройства.
        """
        data = {
            "manufacturer": "",
            "model_name": "",
            "friendly_name": "",
            "model_number": "",
            "serial_number": "",
        }

        try:
            req = urllib.request.Request(location, method="GET")
            req.add_header("User-Agent", "RepeaterMonitor/1.0")
            resp = urllib.request.urlopen(req, timeout=self.description_timeout)
            xml_content = resp.read().decode("utf-8", errors="ignore")

            # Парсим XML
            root = ET.fromstring(xml_content)

            # Ищем device элемент (может быть в разных namespace)
            device_elem = root.find(".//{urn:schemas-upnp-org:device-1-0}device")
            if device_elem is None:
                device_elem = root.find(".//device")

            if device_elem is not None:
                manufacturer = device_elem.find("{urn:schemas-upnp-org:device-1-0}manufacturer")
                if manufacturer is None:
                    manufacturer = device_elem.find("manufacturer")
                if manufacturer is not None and manufacturer.text:
                    data["manufacturer"] = manufacturer.text.strip()

                model_name = device_elem.find("{urn:schemas-upnp-org:device-1-0}modelName")
                if model_name is None:
                    model_name = device_elem.find("modelName")
                if model_name is not None and model_name.text:
                    data["model_name"] = model_name.text.strip()

                friendly_name = device_elem.find("{urn:schemas-upnp-org:device-1-0}friendlyName")
                if friendly_name is None:
                    friendly_name = device_elem.find("friendlyName")
                if friendly_name is not None and friendly_name.text:
                    data["friendly_name"] = friendly_name.text.strip()

                model_number = device_elem.find("{urn:schemas-upnp-org:device-1-0}modelNumber")
                if model_number is None:
                    model_number = device_elem.find("modelNumber")
                if model_number is not None and model_number.text:
                    data["model_number"] = model_number.text.strip()

                serial_number = device_elem.find("{urn:schemas-upnp-org:device-1-0}serialNumber")
                if serial_number is None:
                    serial_number = device_elem.find("serialNumber")
                if serial_number is not None and serial_number.text:
                    data["serial_number"] = serial_number.text.strip()

        except Exception:
            # Если GET не удался, просто возвращаем пустые данные
            pass

        return data
