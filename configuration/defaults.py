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
