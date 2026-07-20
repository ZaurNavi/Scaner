#!/usr/bin/env python3
"""
Repeater Monitor
update_vendors.py

Загрузка актуальной базы производителей MAC (OUI).
v1.7.1a: Синхронизация пути с Configuration Layer.
"""

from pathlib import Path
import urllib.request
import shutil
from configuration import get_config_manager

URL = "https://raw.githubusercontent.com/wireshark/wireshark/master/manuf"


def download():
    config = get_config_manager()
    db_path_str = config.get("fingerprint.vendors.database_path", "vendors/oui.txt")
    output = Path(db_path_str)
    
    output.parent.mkdir(parents=True, exist_ok=True)

    print("Скачивание базы производителей...")
    req = urllib.request.Request(URL, headers={"User-Agent": "RepeaterMonitor/1.0"})

    with urllib.request.urlopen(req, timeout=120) as response:
        with open(output, "wb") as f:
            shutil.copyfileobj(response, f)

    size = output.stat().st_size / 1024 / 1024
    print(f"\nГотово.\nФайл : {output}\nРазмер: {size:.2f} MB")


if __name__ == "__main__":
    print("\nRepeater Monitor\n" + "-" * 60)
    download()
