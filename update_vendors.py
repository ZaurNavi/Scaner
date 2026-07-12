#!/usr/bin/env python3

"""
Repeater Monitor

update_vendors.py

Загрузка актуальной базы производителей MAC (OUI).
"""

from pathlib import Path
import urllib.request
import shutil

URL = "https://raw.githubusercontent.com/wireshark/wireshark/master/manuf"

OUTPUT = Path("vendors/oui.txt")


def download():

    req = urllib.request.Request(
        URL,
        headers={
            "User-Agent": "RepeaterMonitor/1.0"
        },
    )

    with urllib.request.urlopen(req, timeout=120) as response:

        with open(OUTPUT, "wb") as f:

            shutil.copyfileobj(response, f)


def main():

    print()
    print("Repeater Monitor")
    print("-" * 60)

    OUTPUT.parent.mkdir(exist_ok=True)

    print("Скачивание базы производителей...")

    download()

    size = OUTPUT.stat().st_size / 1024 / 1024

    print()
    print("Готово.")
    print(f"Файл : {OUTPUT}")
    print(f"Размер: {size:.2f} MB")


if __name__ == "__main__":
    main()
