"""POC for Phase 5 (Marketing Agent) + Phase 6 (Vision Intelligence).

Uses the local open-source Ollama endpoint by default (services/llm.py);
skipped unless LISTRIX_RUN_LIVE_LLM_TESTS=1 (needs a reachable LLM)."""
import asyncio
import base64
import json
import os

import pytest
import requests
from dotenv import load_dotenv

from services.llm import call_llm, extract_json

load_dotenv()


def _live_llm_enabled():
    return os.environ.get("LISTRIX_RUN_LIVE_LLM_TESTS", "").lower() in ("1", "true", "yes")


pytestmark = pytest.mark.skipif(
    not _live_llm_enabled(),
    reason="requires a reachable LLM endpoint (set LISTRIX_RUN_LIVE_LLM_TESTS=1)",
)


@pytest.mark.asyncio
async def test_marketing_agent():
    print("\n=== TEST 1: Marketing Intelligence Agent (structured analysis) ===")
    system = "You are a resale marketing manager. Respond with a single valid JSON object only."
    prompt = (
        "Item: Sony WH-1000XM4 headphones, condition Like New, cost 180, has photo true, on market 72 hours. "
        "Listing price 180. Produce JSON: {\"performance\":{\"status\":\"good|average|poor\",\"likelihood_of_sale\":number,"
        "\"reason\":str,\"recommended_action\":str},\"suggestions\":[{\"type\":\"reduce_price|improve_title|add_keywords|relist|add_urgency\","
        "\"title\":str,\"detail\":str,\"confidence\":number,\"expected_impact\":str,\"reason\":str,\"params\":{}}]}"
    )
    data = await call_llm(system, prompt)
    assert "performance" in data and "suggestions" in data
    assert data["performance"]["status"] in ("good", "average", "poor")
    print("performance:", data["performance"]["status"], data["performance"]["likelihood_of_sale"])
    print("suggestions:", [s["type"] for s in data["suggestions"]])
    print("TEST 1 PASSED")


@pytest.mark.asyncio
async def test_vision():
    print("\n=== TEST 2: Vision image understanding + value estimation ===")
    url = "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=640&q=80&fm=jpg"
    resp = requests.get(url, headers={"User-Agent": "listrix-poc/1.0"}, timeout=30)
    resp.raise_for_status()
    b64 = base64.b64encode(resp.content).decode("utf-8")
    system = "You are a visual resale expert and pricing analyst. Respond with a single valid JSON object only."
    prompt = (
        "Analyse this product image for a resale marketplace. Respond with ONLY JSON: "
        "{\"item_type\":str,\"category\":str,\"brand\":str|null,\"condition_guess\":str,"
        "\"features\":[str],\"suggested_title\":str,\"suggested_description\":str,"
        "\"value_estimate\":{\"low\":number,\"mid\":number,\"high\":number,\"confidence\":number,\"reasoning\":str}}"
    )
    data = await call_llm(system, prompt, image_b64=b64)
    assert "item_type" in data and "value_estimate" in data
    ve = data["value_estimate"]
    assert all(k in ve for k in ("low", "mid", "high", "confidence"))
    print("identified:", data.get("item_type"), "| category:", data.get("category"), "| brand:", data.get("brand"))
    print("features:", data.get("features"))
    print("value range: $%s-$%s (mid $%s), conf %s" % (ve["low"], ve["high"], ve["mid"], ve["confidence"]))
    print("TEST 2 PASSED")


async def main():
    ok = 0
    try:
        await test_marketing_agent(); ok += 1
    except Exception as e:
        print("TEST 1 FAILED:", type(e).__name__, e)
    try:
        await test_vision(); ok += 1
    except Exception as e:
        print("TEST 2 FAILED:", type(e).__name__, e)
    print(f"\n===== {ok}/2 POC tests passed =====")


if __name__ == "__main__":
    asyncio.run(main())
