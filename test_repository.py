from pathlib import Path
from datetime import datetime
import uuid
from storage.archivist import DatabaseManager, Migrator, Repository
from storage.schema import SnapshotBundle, Scan, Device, Snapshot, Observation, CollectorLog, DeviceStatus, ScanStatus, DeviceType, Source, ObservationType, CollectorStatus

db_path = Path("test_repo_v2.db")
db = DatabaseManager(db_path)
Migrator(db.get_connection()).migrate()
repo = Repository(db)

scan = Scan(id=str(uuid.uuid4()), started_at=datetime.now(), collector_version="2.0", devices_found=1, status=ScanStatus.SUCCESS)
device = Device(mac="AA:BB:CC:DD:EE:FF", first_seen=datetime.now(), last_seen=datetime.now(), status=DeviceStatus.ACTIVE)
snapshot = Snapshot(scan_id=scan.id, device_id=device.id, timestamp=datetime.now(), ip="192.168.1.100", hostname="test-device", device_type=DeviceType.ROUTER, confidence=85)
obs = Observation(snapshot_id=snapshot.id, source=Source.TTL, key="ttl", value="64", obs_type=ObservationType.INTEGER, confidence=40)
log = CollectorLog(scan_id=scan.id, collector_name="ttl_collector", started_at=datetime.now(), duration_ms=15.5, objects_processed=1, status=CollectorStatus.SUCCESS)

bundle = SnapshotBundle(scan_id=scan.id, snapshot=snapshot, scan=scan, device=device, observations=(obs,), collector_log=log)
repo.save_bundle(bundle)
print("✅ Bundle успешно сохранен в БД!")

row = db.get_connection().execute("SELECT ip, hostname, device_type FROM snapshot WHERE id=?", (snapshot.id,)).fetchone()
print(f"Проверка чтения из БД: IP={row[0]}, Hostname={row[1]}, Type={row[2]}")

db.close()
db_path.unlink(missing_ok=True)
print("✅ Repository v1.3.9b успешно протестирован!")
