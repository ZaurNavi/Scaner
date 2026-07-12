"""
mDNS (Bonjour) коллектор.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from zeroconf import Zeroconf, ServiceBrowser

from config import Fingerprint


@dataclass
class MDNSInfo:
    """
    Информация, полученная через mDNS.
    """

    hostname: str = ""

    model: str = ""

    device_type: str = ""

    services: list[str] = field(default_factory=list)


class MDNSListener:
    """
    Слушает mDNS-ответы от всех устройств.
    """

    def __init__(self, target_ips: set[str]):
        self.target_ips = target_ips
        self.results: dict[str, MDNSInfo] = {}

    def add_service(self, zeroconf, service_type, name):
        """
        Вызывается при обнаружении сервиса.
        """

        info = zeroconf.get_service_info(service_type, name)

        if not info or not info.parsed_addresses():
            return

        for ip in info.parsed_addresses():

            if ip not in self.target_ips:
                continue

            if ip not in self.results:
                self.results[ip] = MDNSInfo()

            mdns_info = self.results[ip]

            # Извлекаем hostname
            if info.server and not mdns_info.hostname:
                mdns_info.hostname = info.server.rstrip(".")

            # Извлекаем модель из properties
            props = info.properties

            if not mdns_info.model:
                if b"model" in props:
                    mdns_info.model = props[b"model"].decode("utf-8", errors="ignore")
                elif b"ty" in props:  # Apple использует "ty"
                    mdns_info.model = props[b"ty"].decode("utf-8", errors="ignore")

            # Определяем тип устройства по сервису
            if not mdns_info.device_type:

                if "_apple-mobdev2" in service_type or "_iphone" in service_type:
                    mdns_info.device_type = "iPhone"

                elif "_android" in service_type or "_adb" in service_type:
                    mdns_info.device_type = "Android Device"

                elif "_ipp" in service_type or "_printer" in service_type:
                    mdns_info.device_type = "Printer"

                elif "_googlecast" in service_type:
                    mdns_info.device_type = "Chromecast"

                elif "_airplay" in service_type or "_raop" in service_type:
                    mdns_info.device_type = "AirPlay Device"

                elif "_workstation" in service_type:
                    mdns_info.device_type = "Workstation"

                elif "_smb" in service_type:
                    mdns_info.device_type = "SMB Server"

                elif "_ssh" in service_type:
                    mdns_info.device_type = "SSH Server"

                elif "_http" in service_type or "_https" in service_type:
                    mdns_info.device_type = "HTTP Server"

                # _device-info — дополнительная информация, не тип

            mdns_info.services.append(service_type)

    def update_service(self, zeroconf, service_type, name):
        """
        Вызывается при обновлении сервиса.
        Пустой метод — не обрабатываем обновления.
        """
        pass

    def remove_service(self, zeroconf, service_type, name):
        """
        Вызывается при удалении сервиса.
        Пустой метод — не обрабатываем удаления.
        """
        pass


# Список типов сервисов для сканирования
MDNS_SERVICE_TYPES = [
    "_apple-mobdev2._tcp.local.",
    "_airplay._tcp.local.",
    "_raop._tcp.local.",
    "_googlecast._tcp.local.",
    "_ipp._tcp.local.",
    "_printer._tcp.local.",
    "_http._tcp.local.",
    "_https._tcp.local.",
    "_adb._tcp.local.",
    "_android._tcp.local.",
    "_workstation._tcp.local.",
    "_device-info._tcp.local.",
    "_smb._tcp.local.",
    "_ssh._tcp.local.",
]


def collect_mdns(ips: list[str]) -> dict[str, MDNSInfo]:
    """
    Сканирует всю сеть через mDNS один раз.
    Возвращает {ip: MDNSInfo}.
    """

    if not ips:
        return {}

    target_ips = set(ips)
    zeroconf = Zeroconf()
    listener = MDNSListener(target_ips)

    try:

        # Сохраняем ссылки на browser,
        # иначе объекты будут уничтожены GC и сканирование остановится.
        browsers = []

        for service_type in MDNS_SERVICE_TYPES:
            browser = ServiceBrowser(zeroconf, service_type, listener)
            browsers.append(browser)

        # Ждём ответа от устройств
        time.sleep(Fingerprint.MDNS_TIMEOUT)

    finally:
        zeroconf.close()

    return listener.results
