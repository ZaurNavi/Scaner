#!/usr/bin/env python3
"""
NetBIOS Name Collector — получение имени компьютера через UDP 137.

Использует NBNS (NetBIOS Name Service) для запроса имени.
Отправляет QUERY REQUEST и парсит ответ.
"""

from __future__ import annotations

import socket
import struct
import time
from dataclasses import asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import Fingerprint
from models import Device

from .base import ActiveCollector, FingerprintResult
from storage.active_cache import get as cache_get, set as cache_set


class NetBIOSCollector(ActiveCollector):
    """
    Собирает NetBIOS имена через UDP 137.
    """

    PRIORITY = 47  # После Switch Port
    RELIABILITY = 80

    def __init__(self):
        super().__init__(timeout=1.0)
        self.workers = 32

    def collect(self, device: Device) -> FingerprintResult:
        start_time = time.time()

        # Проверка кэша
        cached = cache_get(device.ip, "netbios")
        if cached:
            return FingerprintResult(**cached, source="netbios", elapsed_ms=0.0)

        if not self.is_available(device):
            elapsed_ms = (time.time() - start_time) * 1000
            result = FingerprintResult(
                source="netbios",
                raw_data={"responded": False, "reason": "device_unavailable"},
                elapsed_ms=elapsed_ms,
            )
            return result

        # Запрос NetBIOS имени
        netbios_data = self._query_netbios(device.ip)
        elapsed_ms = (time.time() - start_time) * 1000

        if netbios_data:
            fingerprint_result = FingerprintResult(
                source="netbios",
                raw_data=netbios_data,
                elapsed_ms=elapsed_ms,
            )
        else:
            fingerprint_result = FingerprintResult(
                source="netbios",
                raw_data={"responded": False, "reason": "no_netbios_response"},
                elapsed_ms=elapsed_ms,
            )

        cache_set(device.ip, "netbios", asdict(fingerprint_result))
        return fingerprint_result

    def _query_netbios(self, ip: str) -> dict | None:
        """
        Отправляет NetBIOS Name Query и парсит ответ.
        """
        try:
            # Создаем UDP сокет
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.timeout)

            # NetBIOS Name Query Request
            # Transaction ID + Flags + Questions + Answer RRs + Authority RRs + Additional RRs
            # + Question Name (encoded) + Question Type + Question Class
            transaction_id = 0x1234
            flags = 0x0000  # Standard query
            questions = 1
            answer_rrs = 0
            authority_rrs = 0
            additional_rrs = 0

            # NetBIOS name encoding: "*" (wildcard) encoded as 32 bytes
            # Each character is split into two nibbles, each nibble + 0x41
            name_encoded = b'\x20'  # Length = 32
            name_encoded += b'CKAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'  # Encoded "*"
            name_encoded += b'\x00'  # Terminator

            question_type = 0x0021  # NB (NetBIOS general Name Service)
            question_class = 0x0001  # IN (Internet)

            # Собираем пакет
            packet = struct.pack(
                '>HHHHHH',
                transaction_id,
                flags,
                questions,
                answer_rrs,
                authority_rrs,
                additional_rrs
            )
            packet += name_encoded
            packet += struct.pack('>HH', question_type, question_class)

            # Отправляем
            sock.sendto(packet, (ip, 137))

            # Получаем ответ
            data, addr = sock.recvfrom(1024)
            sock.close()

            # Парсим ответ
            if len(data) < 12:
                return None

            # Извлекаем имя из ответа
            # Пропускаем заголовок (12 байт) и ищем имя
            offset = 12
            if offset < len(data):
                name_length = data[offset]
                offset += 1
                if name_length > 0 and offset + name_length <= len(data):
                    # Декодируем NetBIOS имя
                    encoded_name = data[offset:offset + name_length]
                    computer_name = self._decode_netbios_name(encoded_name)

                    return {
                        "responded": True,
                        "computer_name": computer_name,
                        "ip": ip,
                    }

            return None

        except (socket.timeout, socket.error):
            return None
        except Exception:
            return None

    def _decode_netbios_name(self, encoded: bytes) -> str:
        """
        Декодирует NetBIOS имя из encoded формата.
        """
        try:
            # NetBIOS encoding: each character is split into two nibbles
            # Each nibble is added to 0x41 ('A')
            decoded = []
            for i in range(0, len(encoded), 2):
                if i + 1 < len(encoded):
                    high = encoded[i] - 0x41
                    low = encoded[i + 1] - 0x41
                    char_code = (high << 4) | low
                    if 32 <= char_code <= 126:  # Printable ASCII
                        decoded.append(chr(char_code))

            # Убираем пробелы в конце
            name = ''.join(decoded).rstrip()
            return name if name else ""
        except Exception:
            return ""

    def scan(self, devices: list[Device], context: dict | None = None, **kwargs) -> dict[str, FingerprintResult]:
        """
        Параллельно собирает NetBIOS имена для всех устройств.
        """
        results: dict[str, FingerprintResult] = {}

        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {
                executor.submit(self.collect, device): device.ip
                for device in devices
            }

            for future in as_completed(futures):
                ip = futures[future]
                try:
                    result = future.result()
                    results[ip] = result
                except Exception:
                    results[ip] = FingerprintResult(source="netbios", elapsed_ms=0.0)

        return results
