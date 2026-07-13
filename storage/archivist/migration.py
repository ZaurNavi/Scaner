import sqlite3

class Migrator:
    def __init__(self, connection: sqlite3.Connection):
        self.conn = connection

    def migrate(self):
        """Создает все таблицы, если их нет. Без потери существующих данных."""
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS device (
                id TEXT PRIMARY KEY,
                mac TEXT UNIQUE NOT NULL,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                status TEXT NOT NULL
            )
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS identity (
                id TEXT PRIMARY KEY,
                device_id TEXT NOT NULL,
                mac TEXT NOT NULL,
                vendor TEXT,
                device_type TEXT,
                fingerprint_hash TEXT,
                base_confidence INTEGER,
                FOREIGN KEY (device_id) REFERENCES device(id)
            )
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS scan (
                id TEXT PRIMARY KEY,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                collector_version TEXT,
                duration_ms REAL,
                devices_found INTEGER,
                status TEXT NOT NULL
            )
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS snapshot (
                id TEXT PRIMARY KEY,
                scan_id TEXT NOT NULL,
                device_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                ip TEXT NOT NULL,
                hostname TEXT,
                os TEXT,
                model TEXT,
                device_type TEXT,
                confidence INTEGER,
                FOREIGN KEY (scan_id) REFERENCES scan(id),
                FOREIGN KEY (device_id) REFERENCES device(id)
            )
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS observation (
                id TEXT PRIMARY KEY,
                snapshot_id TEXT NOT NULL,
                source TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                obs_type TEXT NOT NULL,
                unit TEXT,
                confidence INTEGER,
                FOREIGN KEY (snapshot_id) REFERENCES snapshot(id)
            )
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS evidence (
                id TEXT PRIMARY KEY,
                snapshot_id TEXT NOT NULL,
                description TEXT NOT NULL,
                contribution INTEGER NOT NULL,
                source TEXT NOT NULL,
                details TEXT,
                FOREIGN KEY (snapshot_id) REFERENCES snapshot(id)
            )
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS capability (
                id TEXT PRIMARY KEY,
                snapshot_id TEXT NOT NULL,
                capability TEXT NOT NULL,
                confidence INTEGER,
                FOREIGN KEY (snapshot_id) REFERENCES snapshot(id)
            )
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS session (
                id TEXT PRIMARY KEY,
                device_id TEXT NOT NULL,
                source TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                duration REAL,
                bytes_in INTEGER,
                bytes_out INTEGER,
                flows INTEGER,
                FOREIGN KEY (device_id) REFERENCES device(id)
            )
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS collector_log (
                id TEXT PRIMARY KEY,
                scan_id TEXT NOT NULL,
                collector_name TEXT NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                duration_ms REAL,
                objects_processed INTEGER,
                status TEXT NOT NULL,
                warnings INTEGER,
                error_message TEXT,
                FOREIGN KEY (scan_id) REFERENCES scan(id)
            )
        """)

        self.conn.commit()
