#!/usr/bin/env python3
"""
SSDP/UPnP Collector — обнаружение устройств через multicast.
ES-1.8.3: Возвращает строго List[Observation] через ObservationFactory.
"""
from __future__ import annotations

import socket
import time
import urllib.request
import xml.etree.ElementTree as ET
from models import Device
from .base import ActiveCollector
from configuration import ConfigurationManager
from ..normalization import ObservationFactory


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
    PRIORITY = 60
    RELIABILITY = 70

    def __init__(self, configuration: ConfigurationManager):
        super().__init__(configuration)
        self.timeout = self.config.get("collector.ssdp.timeout", 2.0)
        self.multicast = self.config.get("collector.ssdp.multicast", "239.255.255.250")
        self.port = self.config.get("collector.ssdp.port", 1900)
        self.mx = self.config.get("collector.ssdp.mx", 2)
        self.fetch_description = self.config.get("collector.ssdp.fetch_description", True)
        self.description_timeout = self.config.get("collector.ssdp.description_timeout", 2.0)

    def collect(self, device: Device) -> list:
        """ES-1.8.3: SSDP работает через multicast, collect() не используется."""
        return []

    def scan(self, devices: list[Device], context: dict | None = None, **kwargs) -> list:
        """ES-1.8.3: scan теперь возвращает List[Observation] для всех устройств."""
        if not self.config.get("collector.ssdp.enabled", True):
            return []

        # Отправляем M-SEARCH и собираем ответы
        ssdp_responses = self._send_msearch(devices)
        all_observations = []

        for ip, response_data in ssdp_responses.items():
            # Опционально получаем XML-описание
            if self.fetch_description and response_data.get("location"):
                xml_data = self._fetch_description(response_data["location"])
                response_data.update(xml_data)

            all_observations.append(ObservationFactory.create(
                collector_id=self.source_name,
                protocol="SSDP",
                device_id=ip,
                attribute="ssdp_info",
                value=response_data
            ))

        return all_observations

    def _send_msearch(self, devices: list[Device]) -> dict[str, dict]:
        responses: dict[str, dict] = {}

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(self.timeout)

            request = MSEARCH_REQUEST.format(
                multicast=self.multicast,
                port=self.port,
                mx=self.mx,
            ).encode("utf-8")

            sock.sendto(request, (self.multicast, self.port))

            end_time = time.time() + self.timeout
            target_ips = {d.ip for d in devices}

            while time.time() < end_time:
                try:
                    data, addr = sock.recvfrom(4096)
                    ip = addr[0]

                    if ip in target_ips and ip not in responses:
                        response_data = self._parse_ssdp_response(data.decode("utf-8", errors="ignore"))
                        response_data["responded"] = True
                        responses[ip] = response_data
                except socket.timeout:
                    break
                except Exception:
                    continue

            sock.close()
        except Exception:
            pass

        return responses

    def _parse_ssdp_response(self, response: str) -> dict:
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

            root = ET.fromstring(xml_content)
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
            pass

        return data
