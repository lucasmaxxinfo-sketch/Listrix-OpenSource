"""Unit tests for the shared LLM helper: parsing, retry/backoff, caching."""
import json

import pytest

from services import llm
from services.llm import clear_llm_cache, extract_json


@pytest.fixture(autouse=True)
def reset_cache():
    clear_llm_cache()
    yield
    clear_llm_cache()


@pytest.fixture(autouse=True)
def llm_online(monkeypatch):
    async def ok_probe():
        return {"ok": True, "detail": "stubbed by tests"}

    monkeypatch.setattr(llm, "probe_llm", ok_probe)


def test_extract_json_plain():
    assert extract_json('{"a": 1}') == {"a": 1}


def test_extract_json_with_code_fence():
    assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_extract_json_with_surrounding_text():
    assert extract_json('Here you go: {"a": 1} hope that helps') == {"a": 1}


def test_extract_json_multiple_objects_uses_outermost():
    assert extract_json('{"a": {"b": 2}} tail') == {"a": {"b": 2}}


def test_extract_json_invalid_raises():
    with pytest.raises(json.JSONDecodeError):
        extract_json("no json here")


def test_call_llm_runs_without_api_key(monkeypatch):
    # Local open-source default: no API key required (Ollama accepts any dummy key).
    monkeypatch.setattr(llm, "LLM_API_KEY", None)
    monkeypatch.setattr(llm, "LLM_BASE_URL", "http://localhost:11434/v1")
    calls = {"n": 0}

    async def ok(system_message, prompt, image_b64=None):
        calls["n"] += 1
        return '{"ok": true}'

    monkeypatch.setattr(llm, "_chat_send", ok)
    result = run(llm.call_llm("s", "p"))
    assert result == {"ok": True}
    assert calls["n"] == 1


def test_call_llm_retries_then_succeeds(monkeypatch):
    monkeypatch.setattr(llm, "LLM_API_KEY", "test-key")
    monkeypatch.setattr(llm, "LLM_MAX_RETRIES", 3)
    monkeypatch.setattr(llm, "LLM_RETRY_BASE_DELAY", 0)
    calls = {"n": 0}

    async def flaky(system_message, prompt, image_b64=None):
        calls["n"] += 1
        if calls["n"] < 3:
            raise ConnectionError("transient")
        return '{"ok": true}'

    monkeypatch.setattr(llm, "_chat_send", flaky)
    result = run(llm.call_llm("s", "p"))
    assert result == {"ok": True}
    assert calls["n"] == 3


def test_call_llm_gives_up_after_max_retries(monkeypatch):
    monkeypatch.setattr(llm, "LLM_API_KEY", "test-key")
    monkeypatch.setattr(llm, "LLM_MAX_RETRIES", 2)
    monkeypatch.setattr(llm, "LLM_RETRY_BASE_DELAY", 0)
    calls = {"n": 0}

    async def always_fails(system_message, prompt, image_b64=None):
        calls["n"] += 1
        raise ConnectionError("boom")

    monkeypatch.setattr(llm, "_chat_send", always_fails)
    with pytest.raises(ConnectionError):
        run(llm.call_llm("s", "p"))
    assert calls["n"] == 2


def test_call_llm_does_not_retry_json_decode_error(monkeypatch):
    monkeypatch.setattr(llm, "LLM_API_KEY", "test-key")
    monkeypatch.setattr(llm, "LLM_MAX_RETRIES", 3)
    calls = {"n": 0}

    async def bad_json(system_message, prompt, image_b64=None):
        calls["n"] += 1
        return "not json"

    monkeypatch.setattr(llm, "_chat_send", bad_json)
    with pytest.raises(json.JSONDecodeError):
        run(llm.call_llm("s", "p"))
    assert calls["n"] == 1


def test_call_llm_fails_fast_when_model_offline(monkeypatch):
    async def offline_probe():
        return {"ok": False, "detail": "offline"}

    calls = {"n": 0}

    async def never_called(system_message, prompt, image_b64=None):
        calls["n"] += 1
        return '{"ok": true}'

    monkeypatch.setattr(llm, "probe_llm", offline_probe)
    monkeypatch.setattr(llm, "_chat_send", never_called)
    with pytest.raises(ConnectionError):
        run(llm.call_llm("s", "p"))
    assert calls["n"] == 0


def test_call_llm_caches_identical_text_prompt(monkeypatch):
    monkeypatch.setattr(llm, "LLM_API_KEY", "test-key")
    monkeypatch.setattr(llm, "LLM_CACHE_TTL", 600)
    calls = {"n": 0}

    async def counting(system_message, prompt, image_b64=None):
        calls["n"] += 1
        return '{"answer": 42}'

    monkeypatch.setattr(llm, "_chat_send", counting)
    assert run(llm.call_llm("s", "same prompt")) == {"answer": 42}
    assert run(llm.call_llm("s", "same prompt")) == {"answer": 42}
    assert calls["n"] == 1


def test_call_llm_cache_keyed_by_prompt_and_system(monkeypatch):
    monkeypatch.setattr(llm, "LLM_API_KEY", "test-key")
    monkeypatch.setattr(llm, "LLM_CACHE_TTL", 600)
    calls = {"n": 0}

    async def counting(system_message, prompt, image_b64=None):
        calls["n"] += 1
        return '{"prompt": "' + prompt + '"}'

    monkeypatch.setattr(llm, "_chat_send", counting)
    assert run(llm.call_llm("s1", "p1")) == {"prompt": "p1"}
    assert run(llm.call_llm("s2", "p1")) == {"prompt": "p1"}
    assert run(llm.call_llm("s1", "p2")) == {"prompt": "p2"}
    assert calls["n"] == 3


def test_call_llm_vision_never_cached(monkeypatch):
    monkeypatch.setattr(llm, "LLM_API_KEY", "test-key")
    calls = {"n": 0}

    async def counting(system_message, prompt, image_b64=None):
        calls["n"] += 1
        return '{"vision": "yes"}'

    monkeypatch.setattr(llm, "_chat_send", counting)
    assert run(llm.call_llm("s", "p", image_b64="data:image/jpeg;base64,AAAA")) == {"vision": "yes"}
    assert run(llm.call_llm("s", "p", image_b64="data:image/jpeg;base64,BBBB")) == {"vision": "yes"}
    assert calls["n"] == 2


def run(coro):
    import asyncio

    return asyncio.get_event_loop().run_until_complete(coro)
