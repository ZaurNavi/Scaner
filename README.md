# SISU
### System for Intelligent Scanning and Understanding

> SISU is not just another network scanner.
> It is an attempt to teach software to understand what actually exists inside a network.

## About

SISU (System for Intelligent Scanning and Understanding) is an open-source network discovery and device identification framework.

The project was born from a practical problem. Traditional scanners can discover IP addresses, MAC addresses and open ports, but they often cannot answer the most important question:

**What exactly is this device?**

SISU combines information from multiple independent sources and correlates the collected evidence to identify devices with the highest possible confidence.

Instead of relying on a single protocol, SISU analyzes information from:

- SNMP
- HTTP
- SSDP / UPnP
- mDNS
- DNS
- TCP Fingerprinting
- TTL Analysis
- MAC Vendor (OUI)
- Active Probing
- Correlation Rules

The goal is not simply to scan a network, but to understand it.

## Features

- Intelligent device identification
- Evidence-based correlation engine
- Modular architecture
- Easy to extend with new fingerprint modules
- Vendor database support
- Report generation
- Designed for real enterprise networks

## Why SISU?

Most network scanners stop after discovering hosts.

SISU continues one step further.

It tries to determine:

- What device is this?
- Which operating system is running?
- Who is the vendor?
- Is it a printer, camera, router, IoT device, phone or workstation?
- How confident is this identification?

## Project Status

This project is under active development.

Every new version expands the fingerprint database, improves the correlation engine and increases identification accuracy.

## Philosophy

Networks are becoming larger every year.

The challenge is no longer discovering devices.

The challenge is understanding them.

SISU exists to solve exactly that problem.

---

Created by Zaur Navi
# Repeater Monitor

A modular network scanner and monitoring system written in Python.

## Features

- Network device discovery
- SNMP polling
- NetFlow support
- Vendor detection (OUI)
- Device fingerprinting
- Correlation engine
- Report generation

## Project structure

```
repeater-monitor/
├── fingerprint/      # Fingerprinting engine
├── vendors/          # Vendor database (OUI)
├── config.py         # Configuration
├── monitor.py        # Main application
├── snmp.py           # SNMP module
├── netflow.py        # NetFlow collector
├── report.py         # Report generator
└── requirements.txt
```

## Status

🚧 Work in progress.

The project is under active development.

## Author

Zaur Navi
