#!/usr/bin/env python3
"""Регистрация параметров по умолчанию."""
import ipaddress
from pathlib import Path
from datetime import timedelta
from .registry import ConfigRegistry

def _ip_network_validator(value: str) -> bool:
    try:
        ipaddress.IPv4Network(value)
        return True
    except ValueError:
        return False

def register_defaults():
    """Регистрирует все параметры платформы."""
    
    # Monitor
    ConfigRegistry.register("monitor.scan_interval", int, 60, "Monitor", "Scan interval in seconds")
    ConfigRegistry.register("monitor.worker_threads", int, 4, "Monitor", "Number of worker threads")
    ConfigRegistry.register("monitor.shutdown_timeout", int, 30, "Monitor", "Shutdown timeout in seconds")
    ConfigRegistry.register("monitor.log_level", str, "INFO", "Monitor", "Logging level")
    ConfigRegistry.register("monitor.console_output", bool, True, "Monitor", "Enable console output")
    ConfigRegistry.register("monitor.progress_enabled", bool, True, "Monitor", "Enable progress bars")

    # SNMP Collector
    ConfigRegistry.register("snmp.enabled", bool, True, "SNMP", "Enable SNMP collector")
    ConfigRegistry.register("snmp.community", str, "public", "SNMP", "SNMP community string")
    ConfigRegistry.register("snmp.timeout", int, 5, "SNMP", "SNMP timeout in seconds")
    ConfigRegistry.register("snmp.retries", int, 3, "SNMP", "SNMP retry count")
    ConfigRegistry.register("snmp.max_oids", int, 50, "SNMP", "Max OIDs per request")
    ConfigRegistry.register("snmp.walk_chunk", int, 100, "SNMP", "SNMP walk chunk size")
    ConfigRegistry.register("snmp.cache_ttl", int, 300, "SNMP", "SNMP cache TTL in seconds")

    # NetFlow Collector
    ConfigRegistry.register("netflow.enabled", bool, True, "NetFlow", "Enable NetFlow collector")
    ConfigRegistry.register("netflow.active_window", int, 5, "NetFlow", "Active window in minutes")
    ConfigRegistry.register("netflow.history_days", int, 7, "NetFlow", "History retention in days")
    ConfigRegistry.register("netflow.min_packets", int, 1, "NetFlow", "Minimum packets to consider flow")
    ConfigRegistry.register("netflow.csv_format", bool, False, "NetFlow", "Use CSV format for export")
    ConfigRegistry.register("netflow.flow_directory", str, "/var/nfdump", "NetFlow", "NetFlow directory path")

    # Fingerprint Engine
    ConfigRegistry.register("fingerprint.enabled", bool, True, "Fingerprint", "Enable fingerprinting")
    ConfigRegistry.register("fingerprint.minimum_confidence", float, 0.5, "Fingerprint", "Min confidence threshold")
    ConfigRegistry.register("fingerprint.merge_threshold", float, 0.8, "Fingerprint", "Threshold for merging identities")
    ConfigRegistry.register("fingerprint.vendor_weight", float, 0.3, "Fingerprint", "Weight for vendor matching")
    ConfigRegistry.register("fingerprint.hostname_weight", float, 0.4, "Fingerprint", "Weight for hostname matching")
    ConfigRegistry.register("fingerprint.ttl_weight", float, 0.3, "Fingerprint", "Weight for TTL matching")

    # Knowledge Layer
    ConfigRegistry.register("knowledge.retention_days", int, 30, "Knowledge", "Knowledge retention in days")
    ConfigRegistry.register("knowledge.compression", bool, True, "Knowledge", "Enable knowledge compression")
    ConfigRegistry.register("knowledge.deduplicate", bool, True, "Knowledge", "Deduplicate knowledge facts")
    ConfigRegistry.register("knowledge.cache_size", int, 10000, "Knowledge", "Knowledge cache max size")

    # Repository
    ConfigRegistry.register("repository.database_path", str, "storage/archivist/sisu.db", "Repository", "SQLite database path")
    ConfigRegistry.register("repository.journal_mode", str, "WAL", "Repository", "SQLite journal mode")
    ConfigRegistry.register("repository.vacuum_interval", int, 86400, "Repository", "Vacuum interval in seconds")
    ConfigRegistry.register("repository.backup_enabled", bool, True, "Repository", "Enable automatic backups")

    # Profile Layer
    ConfigRegistry.register("profile.profile_cache", bool, True, "Profile", "Enable profile caching")
    ConfigRegistry.register("profile.profile_cache_size", int, 5000, "Profile", "Max cached profiles")
    ConfigRegistry.register("profile.profile_history_depth", int, 90, "Profile", "Profile history depth in days")

    # Change Detection Layer
    ConfigRegistry.register("diff.diff_cache", bool, True, "Diff", "Enable diff caching")
    ConfigRegistry.register("diff.cache_size", int, 1000, "Diff", "Max cached diffs")
    ConfigRegistry.register("diff.compare_timeout", float, 5.0, "Diff", "Diff comparison timeout in seconds")

    # Domain Event Layer
    ConfigRegistry.register("events.events_enabled", bool, True, "Events", "Enable domain event generation")
    ConfigRegistry.register("events.store_events", bool, True, "Events", "Store events in repository")
    ConfigRegistry.register("events.max_payload_size", int, 4096, "Events", "Max event payload size in bytes")
    ConfigRegistry.register("events.deduplicate_events", bool, True, "Events", "Deduplicate identical events")

    # Logging
    ConfigRegistry.register("logging.level", str, "INFO", "Logging", "Global log level")
    ConfigRegistry.register("logging.rotation_days", int, 7, "Logging", "Log rotation in days")
    ConfigRegistry.register("logging.max_log_size", int, 10485760, "Logging", "Max log file size in bytes")
    ConfigRegistry.register("logging.console", bool, True, "Logging", "Enable console logging")
    ConfigRegistry.register("logging.file", bool, True, "Logging", "Enable file logging")

    # Future layers (placeholders)
    ConfigRegistry.register("telegram.enabled", bool, False, "Telegram", "Enable Telegram bot")
    ConfigRegistry.register("webui.enabled", bool, False, "WebUI", "Enable Web UI")
    ConfigRegistry.register("restapi.enabled", bool, False, "REST API", "Enable REST API")
    ConfigRegistry.register("risk.enabled", bool, False, "Risk", "Enable Risk Engine")
    ConfigRegistry.register("correlation.enabled", bool, False, "Correlation", "Enable Correlation Engine")
