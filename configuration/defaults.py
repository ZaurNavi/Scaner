#!/usr/bin/env python3
"""Регистрация параметров по умолчанию."""
from .registry import ConfigRegistry


def register_defaults(registry: ConfigRegistry):
    """Регистрирует все параметры платформы."""
    
    # Monitor
    registry.register("monitor.scan_interval", int, 60, "Monitor", "Scan interval in seconds", min_value=1)
    registry.register("monitor.worker_threads", int, 4, "Monitor", "Number of worker threads", min_value=1, max_value=32)
    registry.register("monitor.shutdown_timeout", int, 30, "Monitor", "Shutdown timeout in seconds")
    registry.register("monitor.log_level", str, "INFO", "Monitor", "Logging level")
    registry.register("monitor.console_output", bool, True, "Monitor", "Enable console output")
    registry.register("monitor.progress_enabled", bool, True, "Monitor", "Enable progress bars")

    # SNMP Collector
    registry.register("snmp.enabled", bool, True, "SNMP", "Enable SNMP collector")
    registry.register("snmp.community", str, "public", "SNMP", "SNMP community string")
    registry.register("snmp.timeout", int, 5, "SNMP", "SNMP timeout in seconds", min_value=1, max_value=60)
    registry.register("snmp.retries", int, 3, "SNMP", "SNMP retry count", min_value=0, max_value=10)
    registry.register("snmp.max_oids", int, 50, "SNMP", "Max OIDs per request")
    registry.register("snmp.walk_chunk", int, 100, "SNMP", "SNMP walk chunk size")
    registry.register("snmp.cache_ttl", int, 300, "SNMP", "SNMP cache TTL in seconds")

    # NetFlow Collector
    registry.register("netflow.enabled", bool, True, "NetFlow", "Enable NetFlow collector")
    registry.register("netflow.active_window", int, 5, "NetFlow", "Active window in minutes")
    registry.register("netflow.history_days", int, 7, "NetFlow", "History retention in days")
    registry.register("netflow.min_packets", int, 1, "NetFlow", "Minimum packets to consider flow")
    registry.register("netflow.csv_format", bool, False, "NetFlow", "Use CSV format for export")
    registry.register("netflow.flow_directory", str, "/var/nfdump", "NetFlow", "NetFlow directory path")

    # Fingerprint Engine
    registry.register("fingerprint.enabled", bool, True, "Fingerprint", "Enable fingerprinting")
    registry.register("fingerprint.minimum_confidence", float, 0.5, "Fingerprint", "Min confidence threshold", min_value=0.0, max_value=1.0)
    registry.register("fingerprint.merge_threshold", float, 0.8, "Fingerprint", "Threshold for merging identities", min_value=0.0, max_value=1.0)
    registry.register("fingerprint.vendor_weight", float, 0.3, "Fingerprint", "Weight for vendor matching")
    registry.register("fingerprint.hostname_weight", float, 0.4, "Fingerprint", "Weight for hostname matching")
    registry.register("fingerprint.ttl_weight", float, 0.3, "Fingerprint", "Weight for TTL matching")

    # Knowledge Layer
    registry.register("knowledge.retention_days", int, 30, "Knowledge", "Knowledge retention in days")
    registry.register("knowledge.compression", bool, True, "Knowledge", "Enable knowledge compression")
    registry.register("knowledge.deduplicate", bool, True, "Knowledge", "Deduplicate knowledge facts")
    registry.register("knowledge.cache_size", int, 10000, "Knowledge", "Knowledge cache max size", min_value=100, max_value=100000)
    registry.register("knowledge.cache_ttl", int, 3600, "Knowledge", "Knowledge cache TTL in seconds", min_value=60)

    # Repository
    registry.register("repository.database_path", str, "storage/archivist/sisu.db", "Repository", "SQLite database path")
    registry.register("repository.journal_mode", str, "WAL", "Repository", "SQLite journal mode")
    registry.register("repository.vacuum_interval", int, 86400, "Repository", "Vacuum interval in seconds")
    registry.register("repository.backup_enabled", bool, True, "Repository", "Enable automatic backups")

    # Profile Layer
    registry.register("profile.profile_cache", bool, True, "Profile", "Enable profile caching")
    registry.register("profile.profile_cache_size", int, 5000, "Profile", "Max cached profiles")
    registry.register("profile.profile_history_depth", int, 90, "Profile", "Profile history depth in days")

    # Change Detection Layer
    registry.register("diff.diff_cache", bool, True, "Diff", "Enable diff caching")
    registry.register("diff.cache_size", int, 1000, "Diff", "Max cached diffs")
    registry.register("diff.compare_timeout", float, 5.0, "Diff", "Diff comparison timeout in seconds")

    # Domain Event Layer
    registry.register("events.events_enabled", bool, True, "Events", "Enable domain event generation")
    registry.register("events.store_events", bool, True, "Events", "Store events in repository")
    registry.register("events.max_payload_size", int, 4096, "Events", "Max event payload size in bytes")
    registry.register("events.deduplicate_events", bool, True, "Events", "Deduplicate identical events")

    # Logging
    registry.register("logging.level", str, "INFO", "Logging", "Global log level")
    registry.register("logging.rotation_days", int, 7, "Logging", "Log rotation in days")
    registry.register("logging.max_log_size", int, 10485760, "Logging", "Max log file size in bytes")
    registry.register("logging.console", bool, True, "Logging", "Enable console logging")
    registry.register("logging.file", bool, True, "Logging", "Enable file logging")

    # v1.6.9.2: Engines Configuration (для интеграции с Platform Core)
    # Platform Core
    registry.register("platform.enabled", bool, True, "Platform", "Enable Scanner Platform Core")
    
    # Behaviour Engine
    registry.register("behaviour.enabled", bool, True, "Behaviour", "Enable behaviour analysis engine")
    registry.register("behaviour.min_confidence", float, 0.4, "Behaviour", "Min confidence for behaviour facts", min_value=0.0, max_value=1.0)
    
    # Mobility Engine
    registry.register("mobility.enabled", bool, True, "Mobility", "Enable mobility analysis engine")
    
    # Presence Engine
    registry.register("presence.enabled", bool, True, "Presence", "Enable presence analysis engine")
    
    # Usage Engine
    registry.register("usage.enabled", bool, True, "Usage", "Enable usage analysis engine")
    
    # Identity Engine
    registry.register("identity.enabled", bool, True, "Identity", "Enable identity engine")

    # v1.6.9.7: Session Engine Configuration
    registry.register("session.enabled", bool, True, "Session", "Enable session engine")
    registry.register("session.timeout_seconds", int, 1200, "Session", "Session timeout in seconds (20 minutes)", min_value=60)
    registry.register("session.timeline_limit", int, 50, "Session", "Max timeline events per session", min_value=10, max_value=1000)
    registry.register("session.inactivity_minutes", int, 20, "Session", "Inactivity threshold in minutes", min_value=1)
    registry.register("session.merge_window", int, 300, "Session", "Merge window in seconds for session recovery", min_value=60)
    registry.register("session.recovery_enabled", bool, True, "Session", "Enable session recovery on startup")

    # Future layers (placeholders)
    registry.register("telegram.enabled", bool, False, "Telegram", "Enable Telegram bot")
    registry.register("webui.enabled", bool, False, "WebUI", "Enable Web UI")
    registry.register("restapi.enabled", bool, False, "REST API", "Enable REST API")
    registry.register("risk.enabled", bool, False, "Risk", "Enable Risk Engine")
    registry.register("correlation.enabled", bool, False, "Correlation", "Enable Correlation Engine")

    # Repository Layer (v1.6.9.9)
    registry.register("repository.sqlite.journal_mode", str, "WAL", "Repository", "SQLite journal mode")
    registry.register("repository.sqlite.foreign_keys", bool, True, "Repository", "Enable foreign keys")
    registry.register("repository.sqlite.synchronous", str, "NORMAL", "Repository", "SQLite synchronous mode")

    # Cache Layer (v1.6.9.9)
    registry.register("cache.enabled", bool, True, "Cache", "Enable active cache")
    registry.register("cache.ttl.ttl", int, 300, "Cache", "TTL for TTL collector (seconds)")
    registry.register("cache.ttl.tcp", int, 600, "Cache", "TTL for TCP collector (seconds)")
    registry.register("cache.ttl.http", int, 3600, "Cache", "TTL for HTTP collector (seconds)")
    registry.register("cache.ttl.ssdp", int, 1800, "Cache", "TTL for SSDP collector (seconds)")
    registry.register("cache.ttl.snmp", int, 900, "Cache", "TTL for SNMP collector (seconds)")
    registry.register("cache.max_retries", int, 3, "Cache", "Max retry attempts for cache operations", min_value=0, max_value=10)
    registry.register("cache.sqlite.journal_mode", str, "WAL", "Cache", "Cache SQLite journal mode")
    registry.register("cache.sqlite.synchronous", str, "NORMAL", "Cache", "Cache SQLite synchronous mode")

    # Storage Layer (v1.6.9.9)
    registry.register("storage.cache_dir", str, "cache", "Storage", "Cache directory path")
    
    # ==============================================================================
    # v1.7.1: Fingerprint Active Collectors Configuration
    # ==============================================================================
    
    # Global Collector Settings
    registry.register("collector.default.timeout", float, 2.0, "Collector", "Default timeout for collectors", min_value=0.1)
    registry.register("collector.default.workers", int, 32, "Collector", "Default thread pool size", min_value=1, max_value=128)
    registry.register("collector.detection.excluded_ips", str, "127.0.0.1,255.255.255.255", "Collector", "Comma-separated excluded IPs")

    # SNMP Collector
    registry.register("collector.snmp.enabled", bool, True, "Collector", "Enable SNMP collector")
    registry.register("collector.snmp.timeout", float, 2.0, "Collector", "SNMP query timeout", min_value=0.1)
    registry.register("collector.snmp.retries", int, 2, "Collector", "SNMP retries", min_value=0)
    registry.register("collector.snmp.port", int, 161, "Collector", "SNMP port")
    registry.register("collector.snmp.workers", int, 16, "Collector", "SNMP concurrent workers", min_value=1)
    registry.register("collector.snmp.device_timeout", float, 5.0, "Collector", "Max time per device", min_value=1.0)
    registry.register("collector.snmp.skip_if_no_ping", bool, True, "Collector", "Skip SNMP if ping fails")
    registry.register("collector.snmp.communities", str, "public,private,admin", "Collector", "Comma-separated SNMP communities")
    registry.register("collector.snmp.oid.sys_descr", str, "1.3.6.1.2.1.1.1.0", "Collector", "sysDescr OID")
    registry.register("collector.snmp.oid.sys_object_id", str, "1.3.6.1.2.1.1.2.0", "Collector", "sysObjectID OID")
    registry.register("collector.snmp.oid.sys_up_time", str, "1.3.6.1.2.1.1.3.0", "Collector", "sysUpTime OID")
    registry.register("collector.snmp.oid.sys_name", str, "1.3.6.1.2.1.1.5.0", "Collector", "sysName OID")
    registry.register("collector.snmp.oid.sys_services", str, "1.3.6.1.2.1.1.7.0", "Collector", "sysServices OID")
    registry.register("collector.snmp.oid.sys_location", str, "1.3.6.1.2.1.1.6.0", "Collector", "sysLocation OID")
    registry.register("collector.snmp.oid.sys_contact", str, "1.3.6.1.2.1.1.4.0", "Collector", "sysContact OID")

    # TCP Collector
    registry.register("collector.tcp.timeout", float, 1.0, "Collector", "TCP port scan timeout", min_value=0.1)
    registry.register("collector.tcp.max_connections", int, 32, "Collector", "Max concurrent TCP connections per host", min_value=1)
    registry.register("collector.tcp.core_ports", str, "22,53,80,443,445,554,631,9100", "Collector", "Core TCP ports to scan")
    registry.register("collector.tcp.optional_ports", str, "81,139,8080,8081,8443,8291,8728,3389,5357,8008,8009,32400,5000,5001", "Collector", "Optional TCP ports")

    # HTTP Collector
    registry.register("collector.http.timeout", float, 2.0, "Collector", "HTTP request timeout", min_value=0.1)
    registry.register("collector.http.max_body_size", int, 8192, "Collector", "Max HTTP body size to read", min_value=1024)

    # SSH Collector
    registry.register("collector.ssh.timeout", float, 1.0, "Collector", "SSH banner timeout", min_value=0.1)
    registry.register("collector.ssh.workers", int, 64, "Collector", "SSH concurrent workers", min_value=1)
    registry.register("collector.ssh.port", int, 22, "Collector", "SSH port")

    # SMB Collector
    registry.register("collector.smb.timeout", float, 1.0, "Collector", "SMB negotiation timeout", min_value=0.1)
    registry.register("collector.smb.workers", int, 64, "Collector", "SMB concurrent workers", min_value=1)
    registry.register("collector.smb.port", int, 445, "Collector", "SMB port")

    # NTP Collector
    registry.register("collector.ntp.timeout", float, 1.0, "Collector", "NTP query timeout", min_value=0.1)
    registry.register("collector.ntp.workers", int, 32, "Collector", "NTP concurrent workers", min_value=1)
    registry.register("collector.ntp.port", int, 123, "Collector", "NTP port")

    # SSDP Collector
    registry.register("collector.ssdp.enabled", bool, True, "Collector", "Enable SSDP multicast discovery")
    registry.register("collector.ssdp.timeout", float, 2.0, "Collector", "SSDP response timeout", min_value=0.1)
    registry.register("collector.ssdp.multicast", str, "239.255.255.250", "Collector", "SSDP multicast address")
    registry.register("collector.ssdp.port", int, 1900, "Collector", "SSDP port")
    registry.register("collector.ssdp.mx", int, 2, "Collector", "SSDP MX (max wait) seconds")
    registry.register("collector.ssdp.fetch_description", bool, True, "Collector", "Fetch XML description from LOCATION")
    registry.register("collector.ssdp.description_timeout", float, 2.0, "Collector", "XML description fetch timeout", min_value=0.1)

    # NetBIOS Collector
    registry.register("collector.netbios.timeout", float, 1.0, "Collector", "NetBIOS query timeout", min_value=0.1)
    registry.register("collector.netbios.workers", int, 32, "Collector", "NetBIOS concurrent workers", min_value=1)

    # WSD Collector
    registry.register("collector.wsd.timeout", float, 1.5, "Collector", "WSD query timeout", min_value=0.1)
    registry.register("collector.wsd.workers", int, 32, "Collector", "WSD concurrent workers", min_value=1)

    # DNS-SD Collector
    registry.register("collector.dns_sd.timeout", float, 1.5, "Collector", "DNS-SD query timeout", min_value=0.1)
    registry.register("collector.dns_sd.workers", int, 32, "Collector", "DNS-SD concurrent workers", min_value=1)

    # LLDP/CDP Collector
    registry.register("collector.lldp_cdp.timeout", float, 2.0, "Collector", "LLDP/CDP probe timeout", min_value=0.1)
    registry.register("collector.lldp_cdp.workers", int, 16, "Collector", "LLDP/CDP concurrent workers", min_value=1)

    # HTTPS Cert Collector
    registry.register("collector.https_cert.timeout", float, 2.0, "Collector", "HTTPS cert fetch timeout", min_value=0.1)
    registry.register("collector.https_cert.workers", int, 32, "Collector", "HTTPS cert concurrent workers", min_value=1)
    registry.register("collector.https_cert.ports", str, "443,8443,4443", "Collector", "HTTPS ports to check")

    # Favicon Collector
    registry.register("collector.favicon.timeout", float, 2.0, "Collector", "Favicon fetch timeout", min_value=0.1)
    registry.register("collector.favicon.workers", int, 32, "Collector", "Favicon concurrent workers", min_value=1)

    # Banners Collector
    registry.register("collector.banners.timeout", float, 1.0, "Collector", "Banner grab timeout", min_value=0.1)
    registry.register("collector.banners.workers", int, 64, "Collector", "Banner grab concurrent workers", min_value=1)

    # TTL / Ping Collector
    registry.register("collector.ttl.timeout", float, 1.0, "Collector", "Ping timeout", min_value=0.1)
    registry.register("collector.ttl.count", int, 1, "Collector", "Ping packet count", min_value=1)

    # Scapy FP Collector
    registry.register("collector.scapy_fp.timeout", float, 1.0, "Collector", "Scapy probe timeout", min_value=0.1)
    registry.register("collector.scapy_fp.workers", int, 32, "Collector", "Scapy concurrent workers", min_value=1)
    registry.register("collector.scapy_fp.port", int, 80, "Collector", "Scapy target port")

    # Switch Port Collector
    registry.register("collector.switch_port.timeout", float, 2.0, "Collector", "Switch port SNMP timeout", min_value=0.1)
    registry.register("collector.switch_port.workers", int, 16, "Collector", "Switch port concurrent workers", min_value=1)

    # DHCP Cisco Collector
    registry.register("collector.dhcp_cisco.enabled", bool, True, "Collector", "Enable Cisco DHCP collector")
    registry.register("collector.dhcp_cisco.timeout", float, 10.0, "Collector", "SSH connection timeout", min_value=1.0)
    registry.register("collector.dhcp_cisco.cache_ttl", int, 300, "Collector", "DHCP leases cache TTL in seconds", min_value=60)
    registry.register("collector.dhcp_cisco.ip", str, "", "Collector", "Cisco router IP for DHCP")
    registry.register("collector.dhcp_cisco.port", int, 22, "Collector", "Cisco SSH port")
    registry.register("collector.dhcp_cisco.username", str, "", "Collector", "Cisco SSH username")
    registry.register("collector.dhcp_cisco.password", str, "", "Collector", "Cisco SSH password")
    registry.register("collector.dhcp_cisco.ssh_key_path", str, "", "Collector", "Cisco SSH private key path")
    registry.register("collector.dhcp_cisco.enable_password", str, "", "Collector", "Cisco enable password")
    registry.register("collector.dhcp_cisco.network_prefix", str, "192.168.1", "Collector", "Network prefix to filter DHCP leases")
