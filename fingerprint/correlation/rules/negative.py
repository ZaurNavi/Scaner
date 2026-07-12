#!/usr/bin/env python3
"""
Negative Correlation Rules — правила, использующие отсутствие ответов как признак.

Архитектура:
- "ICMP нет + TCP нет" — это не отсутствие данных, а улика
- Позволяет классифицировать "немые" устройства
- Не требует новых сетевых запросов — вся информация уже есть в Evidence
"""

from .base import Rule


def _is_locally_administered_mac(mac: str) -> bool:
    """
    Проверяет, является ли MAC локально администрируемым.
    Это признак MAC randomization (телефоны, планшеты).
    
    Второй символ первого октета:
    - 2, 6, A, E — локально администрируемый (randomized)
    - 0, 4, 8, C — глобально уникальный (OUI)
    """
    if not mac or len(mac) < 2:
        return False
    return mac[1].upper() in ("2", "6", "A", "E")


NEGATIVE_RULES = [

    # ---------------------------------------------------------
    # MAC Randomization — телефон с рандомизированным MAC
    # ---------------------------------------------------------
    Rule(
        name="mac_randomization",
        when=lambda e: (
            e.arp and
            e.flows and
            not e.ping and
            not e.has_open_ports() and
            _is_locally_administered_mac(e.mac)
        ),
        then={
            "os": "Unknown",
            "device_type": "Mobile Device",
            "vendor": "",
            "confidence": 45,
            "reason": "Locally administered MAC + no ICMP/TCP (likely phone with MAC randomization)"
        },
        priority=45
    ),

    # ---------------------------------------------------------
    # Firewall Enabled — устройство отвечает на ping, но блокирует TCP
    # ---------------------------------------------------------
    Rule(
        name="firewall_enabled",
        when=lambda e: (
            e.arp and
            e.flows and
            e.ping and
            not e.has_open_ports() and
            not e.vendor
        ),
        then={
            "os": "Unknown",
            "device_type": "Firewalled Device",
            "vendor": "",
            "confidence": 40,
            "reason": "ICMP OK + no TCP ports (firewall enabled)"
        },
        priority=40
    ),

    # ---------------------------------------------------------
    # Sleeping IoT — очень низкий трафик, молчит
    # ---------------------------------------------------------
    Rule(
        name="sleeping_iot",
        when=lambda e: (
            e.arp and
            e.flows and
            not e.ping and
            not e.has_open_ports() and
            e.megabytes < 1 and
            not e.vendor
        ),
        then={
            "os": "Unknown",
            "device_type": "Sleeping IoT",
            "vendor": "",
            "confidence": 35,
            "reason": "Very low traffic + no ICMP/TCP (sleeping IoT)"
        },
        priority=35
    ),

    # ---------------------------------------------------------
    # Network Infrastructure — много flows, но молчит (switch, AP)
    # ---------------------------------------------------------
    Rule(
        name="network_infrastructure_silent",
        when=lambda e: (
            e.arp and
            e.flows and
            e.flows_count > 100 and
            not e.ping and
            not e.has_open_ports() and
            not e.vendor
        ),
        then={
            "os": "Unknown",
            "device_type": "Network Infrastructure",
            "vendor": "",
            "confidence": 35,
            "reason": "High flows + no ICMP/TCP (switch/AP/repeater)"
        },
        priority=35
    ),

    # ---------------------------------------------------------
    # Passive Endpoint — устройство в сети, но молчит
    # ---------------------------------------------------------
    Rule(
        name="passive_endpoint_with_flows",
        when=lambda e: (
            e.arp and
            e.flows and
            not e.ping and
            not e.has_open_ports() and
            not e.vendor
        ),
        then={
            "os": "Unknown",
            "device_type": "Passive Endpoint",
            "vendor": "",
            "confidence": 30,
            "reason": "ARP + flows + no ICMP/TCP (passive endpoint)"
        },
        priority=30
    ),

    # ---------------------------------------------------------
    # Idle Device — есть в ARP, но нет flows
    # ---------------------------------------------------------
    Rule(
        name="idle_device",
        when=lambda e: (
            e.arp and
            not e.flows and
            not e.ping and
            not e.has_open_ports()
        ),
        then={
            "os": "Unknown",
            "device_type": "Idle Device",
            "vendor": "",
            "confidence": 20,
            "reason": "In ARP but no flows/ICMP/TCP (idle or offline)"
        },
        priority=20
    ),
]
