# SISU
### System for Intelligent Scanning and Understanding

🇬🇧 English | 🇷🇺 [Русская версия](README_RU.md)

---

An intelligent network discovery and device identification framework.
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
/opt/repeater-monitor
├── README.md
├── README_RU.md
├── behaviour
│   ├── __init__.py
│   ├── categories.py
│   ├── constants.py
│   ├── engine.py
│   ├── evaluator.py
│   ├── features.py
│   ├── models.py
│   ├── normalizer.py
│   ├── rules.py
│   └── service.py
├── cache
│   ├── active_cache.db
│   └── devices.db
├── confidence
│   ├── __init__.py
│   ├── categories.py
│   ├── evaluator.py
│   ├── models.py
│   ├── normalizer.py
│   ├── rules.py
│   └── service.py
├── config.py
├── configuration
│   ├── __init__.py
│   ├── defaults.py
│   ├── exceptions.py
│   ├── loader.py
│   ├── manager.py
│   ├── models.py
│   ├── registry.py
│   ├── repository.py
│   ├── serializer.py
│   └── validator.py
├── constants.py
├── docs
│   └── architecture
│       └── domain-model.md
├── events
│   ├── __init__.py
│   ├── comparator.py
│   ├── detector.py
│   ├── engine.py
│   ├── event.py
│   ├── event_type.py
│   ├── persister.py
│   ├── repository.py
│   ├── result.py
│   └── rules
│       ├── __init__.py
│       ├── base.py
│       ├── device_classified.py
│       ├── first_seen.py
│       ├── hostname_changed.py
│       ├── ip_changed.py
│       └── vendor_discovered.py
├── fingerprint
│   ├── __init__.py
│   ├── active
│   │   ├── __init__.py
│   │   ├── banners.py
│   │   ├── base.py
│   │   ├── dhcp_cisco.py
│   │   ├── dns_sd.py
│   │   ├── favicon.py
│   │   ├── http.py
│   │   ├── https_cert.py
│   │   ├── lldp_cdp.py
│   │   ├── netbios.py
│   │   ├── ntp.py
│   │   ├── ping.py
│   │   ├── registry.py
│   │   ├── scapy_fp.py
│   │   ├── smb.py
│   │   ├── snmp.py
│   │   ├── ssdp.py
│   │   ├── ssh.py
│   │   ├── switch_port.py
│   │   ├── tcp.py
│   │   ├── ttl.py
│   │   └── wsd.py
│   ├── analysis.py
│   ├── collectors
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── dns.py
│   │   └── mdns.py
│   ├── controllers
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── omada.py
│   │   └── registry.py
│   ├── correlation
│   │   ├── __init__.py
│   │   ├── capabilities.py
│   │   ├── engine.py
│   │   ├── evidence.py
│   │   ├── evidence_item.py
│   │   ├── result.py
│   │   ├── rules
│   │   ├── rules.py
│   │   └── types.py
│   ├── mac_intelligence.py
│   ├── signatures
│   │   ├── __init__.py
│   │   └── http.py
│   └── vendor_normalizer.py
├── history
│   ├── __init__.py
│   ├── models.py
│   ├── parsers
│   │   ├── __init__.py
│   │   └── omada.py
│   ├── queries.py
│   └── service.py
├── identity
│   ├── __init__.py
│   ├── builder.py
│   ├── engine.py
│   ├── models.py
│   ├── repository.py
│   └── service.py
├── logs
├── mobility
│   ├── __init__.py
│   ├── categories.py
│   ├── constants.py
│   ├── engine.py
│   ├── evaluator.py
│   ├── explain.py
│   ├── features
│   │   └── roaming_feature.py
│   ├── models.py
│   ├── providers
│   │   └── session_provider.py
│   ├── registry.py
│   ├── rules.py
│   └── service.py
├── models.py
├── monitor.py
├── netflow.py
├── presence
│   ├── __init__.py
│   ├── builders
│   │   ├── absolute_metrics.py
│   │   ├── distribution_metrics.py
│   │   └── metrics_builder.py
│   ├── categories.py
│   ├── constants.py
│   ├── engine.py
│   ├── evaluator.py
│   ├── explain.py
│   ├── features
│   │   └── visit_feature.py
│   ├── models.py
│   ├── providers
│   │   └── history_provider.py
│   ├── registry.py
│   ├── rules.py
│   ├── service.py
│   └── timeline.py
├── report.py
├── reports
│   ├── debug_fingerprint.json
│   ├── last_report.csv
│   ├── last_report.json
│   └── last_report.txt
├── requirements.txt
├── run.sh
├── scanner_platform
│   ├── __init__.py
│   ├── behaviour
│   │   ├── __init__.py
│   │   ├── categories.py
│   │   ├── constants.py
│   │   ├── engine.py
│   │   ├── evaluator.py
│   │   ├── features.py
│   │   ├── models.py
│   │   ├── normalizer.py
│   │   ├── rules.py
│   │   └── service.py
│   ├── builders
│   │   ├── base.py
│   │   ├── facts_builder.py
│   │   ├── features_builder.py
│   │   ├── metrics_builder.py
│   │   └── timeline_builder.py
│   ├── cache
│   │   └── platform.py
│   ├── core
│   │   ├── base_engine.py
│   │   ├── bundles.py
│   │   ├── platform.py
│   │   └── platform_context.py
│   ├── coverage
│   │   └── platform.py
│   ├── diff
│   │   ├── __init__.py
│   │   ├── differ.py
│   │   ├── enums.py
│   │   ├── exceptions.py
│   │   ├── indexer.py
│   │   ├── models.py
│   │   └── resolver.py
│   ├── events
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── constants.py
│   │   ├── event_query.py
│   │   ├── event_set.py
│   │   ├── event_types.py
│   │   ├── exceptions.py
│   │   ├── generator.py
│   │   ├── registry.py
│   │   ├── rules
│   │   └── serializer.py
│   ├── facts
│   │   └── models.py
│   ├── knowledge
│   │   ├── __init__.py
│   │   ├── builders
│   │   ├── cache.py
│   │   ├── facade.py
│   │   ├── fact_registry.py
│   │   ├── indexes
│   │   ├── query.py
│   │   ├── registry.py
│   │   ├── service.py
│   │   └── snapshot.py
│   ├── pipeline
│   │   └── engine.py
│   ├── profile
│   │   ├── __init__.py
│   │   ├── builder.py
│   │   ├── cache.py
│   │   ├── capability
│   │   ├── explain
│   │   ├── facets
│   │   ├── models.py
│   │   ├── profile.py
│   │   ├── query
│   │   ├── result.py
│   │   └── service.py
│   ├── registry
│   │   ├── __init__.py
│   │   ├── builder_registry.py
│   │   ├── fact_registry.py
│   │   ├── feature_registry.py
│   │   ├── manager.py
│   │   ├── metric_registry.py
│   │   ├── provider_registry.py
│   │   └── rule_registry.py
│   ├── rules
│   │   └── evaluator.py
│   ├── state
│   │   └── device_state.py
│   ├── timeline
│   │   ├── models.py
│   │   └── provider.py
│   └── validation
│       └── platform.py
├── session
│   ├── __init__.py
│   ├── builder.py
│   ├── engine.py
│   └── models.py
├── snmp.py
├── storage
│   ├── __init__.py
│   ├── active_cache.py
│   ├── archivist
│   │   ├── __init__.py
│   │   ├── archivist.py
│   │   ├── database.py
│   │   ├── migration.py
│   │   ├── repository.py
│   │   ├── sisu.db
│   │   └── snapshot_builder.py
│   ├── device_db.py
│   ├── history.py
│   └── schema
│       ├── __init__.py
│       ├── bundle.py
│       ├── capability.py
│       ├── collector_log.py
│       ├── device.py
│       ├── enums.py
│       ├── evidence.py
│       ├── identity.py
│       ├── observation.py
│       ├── save_result.py
│       ├── scan.py
│       ├── session.py
│       ├── snapshot.py
│       ├── source.py
│       └── version.py
├── test_behaviour.py
├── test_behaviour_platform.py
├── test_configuration.py
├── test_domain_events.py
├── test_domain_events_full.py
├── test_knowledge_layer.py
├── test_platform.py
├── test_profile_differ.py
├── test_repository.py
├── test_unified_profile.py
├── traffic
│   ├── __init__.py
│   ├── collector.py
│   ├── models.py
│   ├── registry.py
│   └── sources
│       ├── base.py
│       ├── netflow.py
│       └── omada.py
├── update_vendors.py
├── usage
│   ├── __init__.py
│   ├── builders
│   │   ├── fact_builder.py
│   │   ├── feature_builder.py
│   │   ├── metrics_builder.py
│   │   └── timeline_builder.py
│   ├── categories.py
│   ├── constants.py
│   ├── engine.py
│   ├── evaluator.py
│   ├── explain.py
│   ├── models.py
│   ├── providers
│   │   └── traffic_provider.py
│   ├── registry.py
│   ├── rules.py
│   └── service.py
├── vendors
│   └── oui.txt
└── vendors.py
```

## Status

🚧 Work in progress.

The project is under active development.

## Author

Zaur Navi
