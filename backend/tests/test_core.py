"""POC: Core AI listing generation for Listrix MVP.
Proves that the OpenAI-compatible LLM layer (services/llm.py) returns a
structured marketplace listing (title, description, suggested_price, hashtags)
from basic item input. Uses the local open-source Ollama endpoint by default;
skipped unless LISTRIX_RUN_LIVE_LLM_TESTS=1 (needs a reachable LLM)."""
import asyncio
import json
import os
import re

import pytest
from dotenv import load_dotenv

from services.llm import call_llm, extract_json

load_dotenv()


def _live_llm_enabled():
    return os.environ.get("LISTRIX_RUN_LIVE_LLM_TESTS", "").lower() in ("1", "true", "yes")


pytestmark = pytest.mark.skipif(
    not _live_llm_enabled(),
    reason="requires a reachable LLM endpoint (set LISTRIX_RUN_LIVE_LLM_TESTS=1)",
)

SYSTEM_MESSAGE = (
    "You are an expert e-commerce copywriter that creates compelling marketplace "
    "listings (like eBay, Facebook Marketplace, TradeMe). "
    "You ALWAYS respond with a single valid JSON object and nothing else. "
    "No markdown, no code fences, no commentary."
)


def build_prompt(item: dict) -> str:
    return (
        "Create a polished marketplace listing for the item below.\n\n"
        f"Title: {item.get('title')}\n"
        f"Description: {item.get('description')}\n"
        f"Category: {item.get('category')}\n"
        f"Asking Price: {item.get('price')}\n\n"
        "Respond with ONLY a JSON object with EXACTLY these keys:\n"
        "{\n"
        '  "listing_title": string (catchy, <= 80 chars),\n'
        '  "listing_description": string (persuasive, 2-4 short paragraphs),\n'
        '  "suggested_price": number (a fair market price as a plain number, no currency symbol),\n'
        '  "hashtags": array of 5-8 short keyword strings without the # symbol\n'
        "}\n"
    )


async def generate_listing(item: dict) -> dict:
    return await call_llm(SYSTEM_MESSAGE, build_prompt(item))


async def run_poc() -> dict:
    item = {"title": "Sony WH-1000XM4 Wireless Headphones", "description": "Like new, all accessories included.",
            "category": "Electronics", "price": 220}
    data = await generate_listing(item)
    assert "listing_title" in data and "suggested_price" in data
    assert isinstance(data.get("hashtags"), list)
    return data


@pytest.mark.asyncio
async def test_core_listing_generation():
    data = await run_poc()
    print("listing_title:", data["listing_title"])
    print("suggested_price:", data["suggested_price"])


if __name__ == "__main__":
    asyncio.run(run_poc())
    print("POC OK")
