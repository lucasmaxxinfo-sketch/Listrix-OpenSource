"""Small pure helpers shared across routes and services."""
import hashlib
from datetime import datetime, timezone


def parse_iso(v):
    if isinstance(v, str):
        try:
            return datetime.fromisoformat(v)
        except ValueError:
            return v
    return v


def to_dt(v):
    if isinstance(v, str):
        try:
            return datetime.fromisoformat(v)
        except ValueError:
            return None
    return v


def hours_since(v):
    dt = to_dt(v)
    if not dt:
        return 0.0
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return round((datetime.now(timezone.utc) - dt).total_seconds() / 3600.0, 1)


def _seed(s):
    return int(hashlib.md5(s.encode()).hexdigest(), 16)
