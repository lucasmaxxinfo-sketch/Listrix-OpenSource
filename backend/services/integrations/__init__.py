"""Connector adapter registry. Real adapters register here; simulated platforms have none."""
from typing import Optional

from services.integrations.base import ConnectorAdapter
from services.integrations.facebook import FacebookAdapter
from services.integrations.gmail import GmailAdapter
from services.integrations.ebay import eBayAdapter
from services.integrations.govcr import GovCROnlineAdapter
from services.integrations.pos import TytnPosAdapter
from services.integrations.stocksix import StocksixAdapter
from services.integrations.trademe import TradeMeAdapter

ADAPTERS = {
    a.platform: a
    for a in (
        TradeMeAdapter(), FacebookAdapter(), GmailAdapter(), StocksixAdapter(),
        eBayAdapter(), GovCROnlineAdapter(), TytnPosAdapter(),
    )
}


def get_adapter(platform: str) -> Optional[ConnectorAdapter]:
    return ADAPTERS.get(platform)
