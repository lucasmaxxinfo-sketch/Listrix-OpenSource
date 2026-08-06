"""Connector adapter seam for real marketplace/communication integrations.

Adapters implement connect/sync and ALWAYS emit approval-gated pending suggestions -
they never mutate listings or post externally without explicit user approval.
Simulated platforms (no adapter) keep the legacy toggle behavior in routes/integrations.py.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class ConnectorAdapter(ABC):
    platform = "base"
    simulated = True

    def is_configured(self) -> bool:
        """Whether the adapter has the credentials it needs to talk to the real service."""
        return False

    @abstractmethod
    async def connect(self, workspace_id: str, conn: Dict[str, Any]) -> Dict[str, Any]:
        """Start the connection flow (e.g. return an OAuth authorize URL)."""

    @abstractmethod
    async def sync(self, workspace_id: str, conn: Dict[str, Any]) -> Dict[str, Any]:
        """Pull external data and return pending, approval-gated suggestions."""

    async def complete_oauth(self, workspace_id: str, oauth_token: str, oauth_verifier: str, conn: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        raise NotImplementedError(f"{self.platform} does not support an OAuth callback")


class EncryptedTokenMixin:
    """Fernet-encrypted token storage shared by real adapters (see trademe.py)."""

    def _fernet(self):
        import base64
        import hashlib

        import config

        if config.CONNECTOR_ENCRYPTION_KEY:
            key = config.CONNECTOR_ENCRYPTION_KEY
        else:
            material = (config.JWT_SECRET or "listrix-dev-secret").encode("utf-8")
            key = base64.urlsafe_b64encode(hashlib.sha256(material).digest()).decode("ascii")
        try:
            from cryptography.fernet import Fernet
        except ImportError:  # pragma: no cover
            raise RuntimeError("cryptography package is not installed")
        return Fernet(key.encode("ascii"))

    def _encrypt(self, payload: dict) -> str:
        import json

        return self._fernet().encrypt(json.dumps(payload).encode("utf-8")).decode("ascii")

    def _decrypt(self, blob: str) -> dict:
        import json

        from cryptography.fernet import InvalidToken

        try:
            return json.loads(self._fernet().decrypt(blob.encode("ascii")))
        except (InvalidToken, ValueError) as e:
            raise RuntimeError(f"Stored connector tokens are unreadable: {e}")
