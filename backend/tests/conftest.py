"""Local test bootstrap.

Forces the in-memory Mongo client (mongomock://) and puts the backend package on
sys.path so `pytest` can import server/models/services regardless of CWD.
"""
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("MONGO_URL", "mongomock://localhost")
os.environ.setdefault("DB_NAME", "listrix_test")
os.environ.setdefault("LLM_RATE_LIMIT_PER_MINUTE", "1000")
os.environ.setdefault("JWT_SECRET", "test-secret-for-listrix-tests-0123456789")
os.environ.setdefault("CORS_ORIGINS", "*")
