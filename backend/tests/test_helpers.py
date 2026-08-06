"""Unit tests for pure helper functions shared across routes and services."""
from datetime import datetime, timezone

from utils import _seed, hours_since, parse_iso, to_dt

# strip_data_url + extract_json live in services/llm (tested in test_llm.py)


def test_parse_iso_roundtrip():
    dt = datetime(2026, 8, 5, 12, 30, 0, tzinfo=timezone.utc)
    assert parse_iso(dt) is dt
    assert parse_iso(dt.isoformat()) == dt


def test_parse_iso_invalid_string_returns_input():
    assert parse_iso("not-a-date") == "not-a-date"


def test_to_dt():
    dt = datetime(2026, 8, 5, 12, 30, 0, tzinfo=timezone.utc)
    assert to_dt(dt.isoformat()) == dt
    assert to_dt("garbage") is None
    assert to_dt(dt) is dt


def test_hours_since_recent():
    now = datetime.now(timezone.utc)
    assert hours_since(now.isoformat()) == 0.0


def test_hours_since_naive_dt_interpreted_utc():
    hours = hours_since(datetime.now(timezone.utc).replace(tzinfo=None).isoformat())
    assert 0.0 <= hours < 1.0


def test_hours_since_garbage_is_zero():
    assert hours_since("nope") == 0.0


def test_seed_is_stable_and_scoped_to_input():
    assert _seed("abc") == _seed("abc")
    assert _seed("abc") != _seed("abd")
    assert 0 <= _seed("abc") < (1 << 128)
