#!/usr/bin/env python3
"""Регистрация параметров по умолчанию для Configuration Layer."""
from .registry import ConfigRegistry


def register_defaults(registry: ConfigRegistry):
    """Регистрирует все параметры платформы."""
    
    # ==============================================================================
    # Monitor
    # ==============================================================================
    registry.register("monitor.scan_interval", int, 60, "Monitor", "Scan interval in seconds", min_value=1)
    registry.register("monitor.worker_threads", int, 4, "Monitor", "Number of worker threads", min_value=1, max_value=32)
    registry.register("monitor.shutdown_timeout", int, 30, "Monitor", "Shutdown timeout in seconds")
    registry.register("monitor.log_level", str, "INFO", "Monitor", "Logging level")
    registry.register("monitor.console_output", bool, True, "Monitor", "Enable console output")
    registry.register("monitor.progress_enabled", bool, True, "Monitor", "Enable progress bars")

    # ==============================================================================
    # SNMP Collector
    # ==============================================================================
    registry.register("snmp.enabled", bool, True, "SNMP", "Enable SNMP collector")
    registry.register("snmp.community", str, "public", "SNMP", "SNMP community string")
    registry.register("snmp.timeout", int, 5, "SNMP", "SNMP timeout in seconds", min_value=1, max_value=60)
    registry.register("snmp.retries", int, 3, "SNMP", "SNMP retry count", min_value=0, max_value=10)
    registry.register("snmp.max_oids", int, 50, "SNMP", "Max OIDs per request")
    registry.register("snmp.walk_chunk", int, 100, "SNMP", "SNMP walk chunk size")
    registry.register("snmp.cache_ttl", int, 300, "SNMP", "SNMP cache TTL in seconds")

    # ==============================================================================
    # NetFlow Collector
    # ==============================================================================
    registry.register("netflow.enabled", bool, True, "NetFlow", "Enable NetFlow collector")
    registry.register("netflow.active_window", int, 5, "NetFlow", "Active window in minutes")
    registry.register("netflow.history_days", int, 7, "NetFlow", "History retention in days")
    registry.register("netflow.min_packets", int, 1, "NetFlow", "Minimum packets to consider flow")
    registry.register("netflow.csv_format", bool, False, "NetFlow", "Use CSV format for export")
    registry.register("netflow.flow_directory", str, "/var/nfdump", "NetFlow", "NetFlow directory path")
    registry.register("netflow.subprocess_timeout", int, 60, "NetFlow", "nfdump subprocess timeout in seconds", min_value=10)
    registry.register("netflow.min_traffic_bytes", int, 200, "NetFlow", "Minimum traffic bytes to consider device active", min_value=0)

    # ==============================================================================
    # Fingerprint Engine (Core)
    # ==============================================================================
    registry.register("fingerprint.enabled", bool, True, "Fingerprint", "Enable fingerprinting")
    registry.register("fingerprint.minimum_confidence", float, 0.5, "Fingerprint", "Min confidence threshold", min_value=0.0, max_value=1.0)
    registry.register("fingerprint.merge_threshold", float, 0.8, "Fingerprint", "Threshold for merging identities", min_value=0.0, max_value=1.0)
    registry.register("fingerprint.vendor_weight", float, 0.3, "Fingerprint", "Weight for vendor matching")
    registry.register("fingerprint.hostname_weight", float, 0.4, "Fingerprint", "Weight for hostname matching")
    registry.register("fingerprint.ttl_weight", float, 0.3, "Fingerprint", "Weight for TTL matching")
    registry.register("fingerprint.vendors.database_path", str, "vendors/oui.txt", "Fingerprint", "Path to IEEE OUI database file")

    # ==============================================================================
    # Knowledge Layer
    # ==============================================================================
    registry.register("knowledge.retention_days", int, 30, "Knowledge", "Knowledge retention in days")
    registry.register("knowledge.compression", bool, True, "Knowledge", "Enable knowledge compression")
    registry.register("knowledge.deduplicate", bool, True, "Knowledge", "Deduplicate knowledge facts")
    registry.register("knowledge.cache_size", int, 10000, "Knowledge", "Knowledge cache max size", min_value=100, max_value=100000)
    registry.register("knowledge.cache_ttl", int, 3600, "Knowledge", "Knowledge cache TTL in seconds", min_value=60)

    # ==============================================================================
    # Repository Layer
    # ==============================================================================
    registry.register("repository.database_path", str, "storage/archivist/sisu.db", "Repository", "SQLite database path")
    registry.register("repository.journal_mode", str, "WAL", "Repository", "SQLite journal mode")
    registry.register("repository.vacuum_interval", int, 86400, "Repository", "Vacuum interval in seconds")
    registry.register("repository.backup_enabled", bool, True, "Repository", "Enable automatic backups")
    registry.register("repository.sqlite.journal_mode", str, "WAL", "Repository", "SQLite journal mode")
    registry.register("repository.sqlite.foreign_keys", bool, True, "Repository", "Enable foreign keys")
    registry.register("repository.sqlite.synchronous", str, "NORMAL", "Repository", "SQLite synchronous mode")

    # ==============================================================================
    # Profile Layer
    # ==============================================================================
    registry.register("profile.profile_cache", bool, True, "Profile", "Enable profile caching")
    registry.register("profile.profile_cache_size", int, 5000, "Profile", "Max cached profiles")
    registry.register("profile.profile_history_depth", int, 90, "Profile", "Profile history depth in days")

    # ==============================================================================
    # Change Detection Layer
    # ==============================================================================
    registry.register("diff.diff_cache", bool, True, "Diff", "Enable diff caching")
    registry.register("diff.cache_size", int, 1000, "Diff", "Max cached diffs")
    registry.register("diff.compare_timeout", float, 5.0, "Diff", "Diff comparison timeout in seconds")

    # ==============================================================================
    # Domain Event Layer
    # ==============================================================================
    registry.register("events.events_enabled", bool, True, "Events", "Enable domain event generation")
    registry.register("events.store_events", bool, True, "Events", "Store events in repository")
    registry.register("events.max_payload_size", int, 4096, "Events", "Max event payload size in bytes")
    registry.register("events.deduplicate_events", bool, True, "Events", "Deduplicate identical events")

    # ==============================================================================
    # Logging
    # ==============================================================================
    registry.register("logging.level", str, "INFO", "Logging", "Global log level")
    registry.register("logging.rotation_days", int, 7, "Logging", "Log rotation in days")
    registry.register("logging.max_log_size", int, 10485760, "Logging", "Max log file size in bytes")
    registry.register("logging.console", bool, True, "Logging", "Enable console logging")
    registry.register("logging.file", bool, True, "Logging", "Enable file logging")

    # ==============================================================================
    # Platform Core & Engines (v1.6.9.2)
    # ==============================================================================
    registry.register("platform.enabled", bool, True, "Platform", "Enable Scanner Platform Core")
    registry.register("behaviour.enabled", bool, True, "Behaviour", "Enable behaviour analysis engine")
    registry.register("behaviour.min_confidence", float, 0.4, "Behaviour", "Min confidence for behaviour facts", min_value=0.0, max_value=1.0)
    registry.register("mobility.enabled", bool, True, "Mobility", "Enable mobility analysis engine")
    registry.register("presence.enabled", bool, True, "Presence", "Enable presence analysis engine")
    registry.register("usage.enabled", bool, True, "Usage", "Enable usage analysis engine")
    registry.register("identity.enabled", bool, True, "Identity", "Enable identity engine")
    registry.register("confidence.enabled", bool, True, "Confidence", "Enable confidence engine")
    registry.register("confidence.max_score", int, 100, "Confidence", "Max confidence score", min_value=0, max_value=100)

    # ==============================================================================
    # Session Engine (v1.6.9.7)
    # ==============================================================================
    registry.register("session.enabled", bool, True, "Session", "Enable session engine")
    registry.register("session.timeout_seconds", int, 1200, "Session", "Session timeout in seconds (20 minutes)", min_value=60)
    registry.register("session.timeline_limit", int, 50, "Session", "Max timeline events per session", min_value=10, max_value=1000)
    registry.register("session.inactivity_minutes", int, 20, "Session", "Inactivity threshold in minutes", min_value=1)
    registry.register("session.merge_window", int, 300, "Session", "Merge window in seconds for session recovery", min_value=60)
    registry.register("session.recovery_enabled", bool, True, "Session", "Enable session recovery on startup")

    # ==============================================================================
    # Cache & Storage Layer (v1.6.9.9)
    # ==============================================================================
    registry.register("cache.enabled", bool, True, "Cache", "Enable active cache")
    registry.register("cache.ttl.ttl", int, 300, "Cache", "TTL for TTL collector (seconds)", min_value=60)
    registry.register("cache.ttl.tcp", int, 600, "Cache", "TTL for TCP collector (seconds)", min_value=60)
    registry.register("cache.ttl.http", int, 3600, "Cache", "TTL for HTTP collector (seconds)", min_value=60)
    registry.register("cache.ttl.ssdp", int, 1800, "Cache", "TTL for SSDP collector (seconds)", min_value=60)
    registry.register("cache.ttl.snmp", int, 900, "Cache", "TTL for SNMP collector (seconds)", min_value=60)
    registry.register("cache.max_retries", int, 3, "Cache", "Max retry attempts for cache operations", min_value=0, max_value=10)
    registry.register("cache.sqlite.journal_mode", str, "WAL", "Cache", "Cache SQLite journal mode")
    registry.register("cache.sqlite.synchronous", str, "NORMAL", "Cache", "Cache SQLite synchronous mode")
    registry.register("storage.cache_dir", str, "cache", "Storage", "Cache directory path")

    # ==============================================================================
    # Fingerprint Active Collectors (v1.7.1)
    # ==============================================================================
    registry.register("collector.default.timeout", float, 2.0, "Collector", "Default timeout for collectors", min_value=0.1)
    registry.register("collector.default.workers", int, 32, "Collector", "Default thread pool size", min_value=1, max_value=128)
    
    # SNMP Collector specific
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

    # SSH, SMB, NTP, LLDP/CDP, HTTPS, Favicon, Banners
    registry.register("collector.ssh.timeout", float, 1.0, "Collector", "SSH banner timeout", min_value=0.1)
    registry.register("collector.ssh.workers", int, 64, "Collector", "SSH concurrent workers", min_value=1)
    registry.register("collector.ssh.port", int, 22, "Collector", "SSH port")
    registry.register("collector.smb.timeout", float, 1.0, "Collector", "SMB negotiation timeout", min_value=0.1)
    registry.register("collector.smb.workers", int, 64, "Collector", "SMB concurrent workers", min_value=1)
    registry.register("collector.smb.port", int, 445, "Collector", "SMB port")
    registry.register("collector.ntp.timeout", float, 1.0, "Collector", "NTP query timeout", min_value=0.1)
    registry.register("collector.ntp.workers", int, 32, "Collector", "NTP concurrent workers", min_value=1)
    registry.register("collector.ntp.port", int, 123, "Collector", "NTP port")
    registry.register("collector.lldp_cdp.timeout", float, 2.0, "Collector", "LLDP/CDP probe timeout", min_value=0.1)
    registry.register("collector.lldp_cdp.workers", int, 16, "Collector", "LLDP/CDP concurrent workers", min_value=1)
    registry.register("collector.https_cert.timeout", float, 2.0, "Collector", "HTTPS cert fetch timeout", min_value=0.1)
    registry.register("collector.https_cert.workers", int, 32, "Collector", "HTTPS cert concurrent workers", min_value=1)
    registry.register("collector.https_cert.ports", str, "443,8443,4443", "Collector", "HTTPS ports to check")
    registry.register("collector.favicon.timeout", float, 2.0, "Collector", "Favicon fetch timeout", min_value=0.1)
    registry.register("collector.favicon.workers", int, 32, "Collector", "Favicon concurrent workers", min_value=1)
    registry.register("collector.banners.timeout", float, 1.0, "Collector", "Banner grab timeout", min_value=0.1)
    registry.register("collector.banners.workers", int, 64, "Collector", "Banner grab concurrent workers", min_value=1)

    # ==============================================================================
    # Fingerprint Passive Collectors (ES-1.8.4 - LLMNR)
    # ==============================================================================
    # DNS Collector (passive reverse lookup)
    registry.register("fingerprint.collectors.dns.enabled", bool, True, "Fingerprint DNS", "Enable DNS passive collector")
    registry.register("fingerprint.collectors.dns.workers", int, 32, "Fingerprint DNS", "DNS concurrent workers", min_value=1, max_value=128)
    
    # mDNS Collector
    registry.register("fingerprint.collectors.mdns.enabled", bool, True, "Fingerprint mDNS", "Enable mDNS passive collector")
    registry.register("fingerprint.collectors.mdns.timeout", float, 2.0, "Fingerprint mDNS", "mDNS listen timeout", min_value=0.5, max_value=10.0)
    
    # LLMNR Collector (ES-1.8.4)
    registry.register("fingerprint.collectors.llmnr.enabled", bool, True, "Fingerprint LLMNR", "Enable LLMNR passive collector")
    registry.register("fingerprint.collectors.llmnr.timeout", float, 0.5, "Fingerprint LLMNR", "LLMNR socket timeout in seconds", min_value=0.1, max_value=5.0)
    registry.register("fingerprint.collectors.llmnr.operation_timeout", float, 2.0, "Fingerprint LLMNR", "LLMNR total operation timeout", min_value=0.5, max_value=10.0)
    registry.register("fingerprint.collectors.llmnr.workers", int, 32, "Fingerprint LLMNR", "LLMNR concurrent workers", min_value=1, max_value=128)
    registry.register("fingerprint.collectors.llmnr.port", int, 5355, "Fingerprint LLMNR", "LLMNR UDP port")
    registry.register("fingerprint.collectors.llmnr.multicast", bool, True, "Fingerprint LLMNR", "Enable LLMNR multicast listening")

    # TTL / Ping / Scapy
    registry.register("collector.ttl.timeout", float, 1.0, "Collector", "Ping timeout", min_value=0.1)
    registry.register("collector.ttl.count", int, 1, "Collector", "Ping packet count", min_value=1)
    registry.register("collector.scapy_fp.timeout", float, 1.0, "Collector", "Scapy probe timeout", min_value=0.1)
    registry.register("collector.scapy_fp.workers", int, 32, "Collector", "Scapy concurrent workers", min_value=1)
    registry.register("collector.scapy_fp.port", int, 80, "Collector", "Scapy target port")

    # Switch Port / DHCP Cisco
    registry.register("collector.switch_port.timeout", float, 2.0, "Collector", "Switch port SNMP timeout", min_value=0.1)
    registry.register("collector.switch_port.workers", int, 16, "Collector", "Switch port concurrent workers", min_value=1)
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

    # SSDP / NetBIOS / WSD / DNS-SD
    registry.register("collector.ssdp.enabled", bool, True, "Collector", "Enable SSDP multicast discovery")
    registry.register("collector.ssdp.timeout", float, 2.0, "Collector", "SSDP response timeout", min_value=0.1)
    registry.register("collector.ssdp.multicast", str, "239.255.255.250", "Collector", "SSDP multicast address")
    registry.register("collector.ssdp.port", int, 1900, "Collector", "SSDP port")
    registry.register("collector.ssdp.mx", int, 2, "Collector", "SSDP MX (max wait) seconds")
    registry.register("collector.ssdp.fetch_description", bool, True, "Collector", "Fetch XML description from LOCATION")
    registry.register("collector.ssdp.description_timeout", float, 2.0, "Collector", "XML description fetch timeout", min_value=0.1)
    registry.register("collector.netbios.timeout", float, 1.0, "Collector", "NetBIOS query timeout", min_value=0.1)
    registry.register("collector.netbios.workers", int, 32, "Collector", "NetBIOS concurrent workers", min_value=1)
    registry.register("collector.wsd.timeout", float, 1.5, "Collector", "WSD query timeout", min_value=0.1)
    registry.register("collector.wsd.workers", int, 32, "Collector", "WSD concurrent workers", min_value=1)
    registry.register("collector.dns_sd.timeout", float, 1.5, "Collector", "DNS-SD query timeout", min_value=0.1)
    registry.register("collector.dns_sd.workers", int, 32, "Collector", "DNS-SD concurrent workers", min_value=1)
    registry.register("collector.dns.workers", int, 32, "Collector", "Concurrent workers for DNS resolution", min_value=1)
    registry.register("collector.mdns.timeout", float, 2.0, "Collector", "mDNS scan timeout in seconds", min_value=0.5)

    # ==============================================================================
    # Final Infrastructure (v1.7.1a)
    # ==============================================================================
    registry.register("network.prefix", str, "192.168.1", "Network", "Network prefix for filtering (e.g., 192.168.1)")
    registry.register("collector.detection.excluded_ips", str, "127.0.0.1,255.255.255.255", "Network", "Comma-separated excluded IPs")

    # Future layers (placeholders)
    registry.register("telegram.enabled", bool, False, "Telegram", "Enable Telegram bot")
    registry.register("webui.enabled", bool, False, "WebUI", "Enable Web UI")
    registry.register("restapi.enabled", bool, False, "REST API", "Enable REST API")
    registry.register("risk.enabled", bool, False, "Risk", "Enable Risk Engine")
    registry.register("correlation.enabled", bool, False, "Correlation", "Enable Correlation Engine")
    
    # ==============================================================================
    # Normalization Layer (ES-1.8.1)
    # ==============================================================================
    registry.register("fingerprint.normalization.enabled", bool, True, "Fingerprint", "Enable normalization layer")
    registry.register("fingerprint.normalization.unknown_policy", str, "log", "Fingerprint", "Policy for unknown observations: keep, drop, log")
    registry.register("fingerprint.normalization.batch_size", int, 1000, "Fingerprint", "Batch size for normalize_many()", min_value=1)
