import csv
from pathlib import Path


def load(data_dir):
    """Load every CSV in data_dir into a dict of table name -> list of row dicts."""
    tables = {}
    for path in sorted(Path(data_dir).glob("*.csv")):
        with open(path, newline="") as f:
            tables[path.stem] = list(csv.DictReader(f))
    return tables


def normalize_email(email):
    return (email or "").strip().lower()


def normalize_phone(phone):
    digits = "".join(ch for ch in (phone or "") if ch.isdigit())
    return digits[-10:]
