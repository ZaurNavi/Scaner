#!/usr/bin/env python3
"""
Repeater Monitor
snmp.py

Получение ARP-таблицы Cisco по SNMP.

Возвращает словарь:

{
    "192.168.1.103": "5E:B3:B7:0F:DA:7F",
}
"""

from __future__ import annotations

import subprocess
import sys

from config import Cisco
from config import Detection
from config import Network

from constants import ARP_OID


def format_mac(hex_string: str) -> str:
    """
    Hex-STRING:

    5E B3 B7 0F DA 7F

    →

    5E:B3:B7:0F:DA:7F
    """

    return ":".join(
        part.upper()
        for part in hex_string.strip().split()
    )


def get_arp_table() -> dict[str, str]:

    cmd = [

        "snmpwalk",

        "-v2c",

        "-c",
        Cisco.COMMUNITY,

        "-t",
        str(Cisco.TIMEOUT),

        "-r",
        str(Cisco.RETRIES),

        Cisco.IP,

        ARP_OID,

    ]

    result = subprocess.run(

        cmd,

        capture_output=True,

        text=True,

    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())

    arp = {}

    for line in result.stdout.splitlines():

        if "Hex-STRING:" not in line:
            continue

        left, right = line.split("=", 1)

        ip = ".".join(left.strip().split(".")[-4:])

        if not ip.startswith(Network.PREFIX):
            continue

        if ip in Detection.EXCLUDED_IPS:
            continue

        mac = right.replace("Hex-STRING:", "").strip()

        arp[ip] = format_mac(mac)

    return arp


def main():

    print()

    print(App.NAME if False else "Repeater Monitor")
    print("-" * 60)

    print(f"Cisco IP : {Cisco.IP}")
    print(f"Network  : {Network.SUBNET}")

    print()

    try:

        arp = get_arp_table()

    except Exception as exc:

        print("Ошибка SNMP:")

        print(exc)

        sys.exit(1)

    print(f"Получено устройств: {len(arp)}")

    print()

    for ip in sorted(arp):

        print(f"{ip:15} -> {arp[ip]}")

    print()

    print("SNMP модуль работает успешно.")


if __name__ == "__main__":
    main()
