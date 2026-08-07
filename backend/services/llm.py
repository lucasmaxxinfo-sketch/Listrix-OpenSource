"""Shared LLM access: strict-JSON parsing, retry with exponential backoff, response caching.

Uses the official `openai` SDK (an open-source library) against any OpenAI-compatible endpoint.
The default is a LOCAL open-source Ollama server — no API key, no paid service:
  LLM_BASE_URL  - defaults to http://localhost:11434/v1 (local Ollama)
  LLM_MODEL     - defaults to llama3.2-vision (open weights; swap for any local model)
  LLM_API_KEY   - optional; local servers accept any dummy key
Vision payloads go through the same endpoint as image_url inputs (OpenAI-compatible).
"""
import asyncio
import hashlib
import json
import logging
import re
import time

from config import (
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_CACHE_MAX_ENTRIES,
    LLM_CACHE_TTL,
    LLM_MAX_RETRIES,
    LLM_MODEL,
    LLM_RETRY_BASE_DELAY,
)

try:
    from openai import AsyncOpenAI

    _LLM_AVAILABLE = True
except ImportError:  # pragma: no cover - openai SDK not installed
    _LLM_AVAILABLE = False

logger = logging.getLogger(__name__)

_cache = {}


def strip_data_url(b):
    return b.split("base64,", 1)[1] if b and "base64," in b else b


def extract_json(text):
    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
    s, e = text.find("{"), text.rfind("}")
    if s != -1 and e != -1:
        text = text[s:e + 1]
    return json.loads(text)


def _cache_key(system_message, prompt):
    h = hashlib.sha256()
    h.update((system_message or "").encode("utf-8"))
    h.update(b"\x00")
    h.update((prompt or "").encode("utf-8"))
    return h.hexdigest()


def _get_cached(key):
    item = _cache.get(key)
    if not item:
        return None
    expires, result = item
    if expires < time.monotonic():
        _cache.pop(key, None)
        return None
    return result


def _set_cached(key, result):
    if len(_cache) >= LLM_CACHE_MAX_ENTRIES:
        now = time.monotonic()
        for k in list(_cache):
            if _cache[k][0] < now:
                _cache.pop(k, None)
        if len(_cache) >= LLM_CACHE_MAX_ENTRIES:
            _cache.clear()
    _cache[key] = (time.monotonic() + LLM_CACHE_TTL, result)


def clear_llm_cache():
    _cache.clear()


def _client():
    return AsyncOpenAI(api_key=LLM_API_KEY or "sk-local", base_url=LLM_BASE_URL or None, timeout=60.0)


_probe_cache = {}


async def probe_llm():
    """Cheap reachability probe of the configured LLM endpoint (cached ~30s).

    Used by the UI status banner so users see a clear 'AI brain offline' state
    instead of confusing per-request errors. Never caches model output.
    """
    now = time.monotonic()
    cached = _probe_cache.get("last")
    if cached and cached[0] + 30 > now:
        return cached[1]
    if not _LLM_AVAILABLE:
        result = {"ok": False, "detail": "openai package is not installed"}
    else:
        try:
            probe_client = AsyncOpenAI(api_key=LLM_API_KEY or "sk-local",
                                       base_url=LLM_BASE_URL or None, timeout=8.0)
            await probe_client.chat.completions.create(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": "Reply with exactly: OK"}],
                max_tokens=4,
            )
            result = {"ok": True, "detail": "AI model is reachable"}
        except Exception as e:  # noqa: BLE001 - any failure means the model is offline
            result = {"ok": False, "detail": str(e) or "model server is not reachable"}
    _probe_cache["last"] = (now, result)
    return result


async def _chat_send(system_message, prompt, image_b64=None):
    if not _LLM_AVAILABLE:
        raise RuntimeError("openai package is not installed (pip install openai)")
    if image_b64:
        content = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{strip_data_url(image_b64)}"}},
        ]
    else:
        content = prompt
    resp = await _client().chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": content},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content


async def call_llm(system_message, prompt, image_b64=None):
    # No API-key gate: the default endpoint is a local open-source Ollama server that accepts
    # any key. A connection error simply means the local model server is not running yet.
    if image_b64:
        # Vision payloads are large and one-shot: never cached.
        return extract_json(await _chat_send(system_message, prompt, image_b64))
    key = _cache_key(system_message, prompt)
    cached = _get_cached(key)
    if cached is not None:
        logger.info("LLM response cache hit")
        return cached
    last_error = None
    for attempt in range(1, LLM_MAX_RETRIES + 1):
        try:
            result = extract_json(await _chat_send(system_message, prompt, None))
            _set_cached(key, result)
            return result
        except json.JSONDecodeError:
            # Deterministic prompt/parse problem - retrying will not help.
            raise
        except Exception as e:
            last_error = e
            logger.warning(f"LLM call attempt {attempt}/{LLM_MAX_RETRIES} failed: {e}")
            if attempt < LLM_MAX_RETRIES:
                await asyncio.sleep(LLM_RETRY_BASE_DELAY * (2 ** (attempt - 1)))
    raise last_error
