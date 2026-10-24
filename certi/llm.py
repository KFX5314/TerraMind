"""Thin Claude wrapper: JSON-schema outputs, disk cache keyed by request hash, usage/cost ledger, concurrency cap."""

from __future__ import annotations

import asyncio
import base64
import contextvars
import hashlib
import json
import os
import threading
import time
import weakref
from pathlib import Path
from typing import Any

import anthropic
from dotenv import load_dotenv

from . import paths

load_dotenv(paths.ROOT / ".env")

MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-5-5")
MAX_CONCURRENCY = int(os.environ.get("MAX_MODEL_CONCURRENCY", "8"))
MAX_RUN_USD = float(os.environ.get("MAX_RUN_USD", "40"))
USE_FALLBACKS = os.environ.get("CLAUDE_FALLBACKS", "1") == "1"

# $ per 1M tokens: input, output, cache read, cache write (1.25x input)
PRICES = {
    "claude-opus-5-5": (4.0, 20.0, 0.20, 5.0),
    "claude-sonnet-5-5": (2.0, 10.0, 0.20, 2.5),
    "claude-haiku-5-5": (0.10, 0.50, 0.01, 0.125),
}
LEDGER = paths.DATA / "usage.jsonl"

def role_model(role: str) -> str:
    """Model for a pipeline role (profile, screen, extract, audit, judge): CLAUDE_<ROLE>_MODEL, else CLAUDE_MODEL."""
    return os.environ.get(f"CLAUDE_{role.upper()}_MODEL") or MODEL


def role_effort(role: str, default: str = "high") -> str:
    """Effort for a pipeline role: CLAUDE_<ROLE>_EFFORT, else the given default."""
    return os.environ.get(f"CLAUDE_{role.upper()}_EFFORT") or default


class LLMError(RuntimeError):
    pass


class Truncated(LLMError):
    pass


class Budget:
    """Spend of one run (thread-safe). llm.run() gives every run its own, so concurrent server jobs neither share nor
    inherit each other's spend."""

    def __init__(self, cap: float):
        self.cap = cap
        self.spent = 0.0
        self._lock = threading.Lock()

    def add(self, usd: float) -> None:
        with self._lock:
            self.spent += usd


_budget: contextvars.ContextVar[Budget | None] = contextvars.ContextVar("certi_budget", default=None)
_fallback_budget = Budget(MAX_RUN_USD)  # calls made outside llm.run()


def budget() -> Budget:
    return _budget.get() or _fallback_budget


def spent() -> float:
    return budget().spent


# Client and semaphore are bound to an event loop; keep one pair per running loop instead of resetting globals,
# so two runs in different threads cannot clobber each other's.
_loops: "weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, dict]" = weakref.WeakKeyDictionary()


def _loop_state() -> dict:
    loop = asyncio.get_running_loop()
    st = _loops.get(loop)
    if st is None:
        st = {"client": anthropic.AsyncAnthropic(max_retries=6, timeout=900), "sem": asyncio.Semaphore(MAX_CONCURRENCY)}
        _loops[loop] = st
    return st


def client() -> anthropic.AsyncAnthropic:
    return _loop_state()["client"]


def _semaphore() -> asyncio.Semaphore:
    return _loop_state()["sem"]


def image_block(path: Path) -> dict:
    media = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".gif": "image/gif"}[
        path.suffix.lower()
    ]
    return {"type": "image", "source": {"type": "base64", "media_type": media,
                                        "data": base64.standard_b64encode(path.read_bytes()).decode()}}


def cost(model: str, usage: Any) -> float:
    pin, pout, pread, pwrite = PRICES.get(model, PRICES["claude-opus-5-5"])
    return (
        (usage.input_tokens or 0) * pin
        + (usage.output_tokens or 0) * pout
        + (getattr(usage, "cache_read_input_tokens", 0) or 0) * pread
        + (getattr(usage, "cache_creation_input_tokens", 0) or 0) * pwrite
    ) / 1e6


def _key(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def total_spent() -> float:
    if not LEDGER.exists():
        return 0.0
    return sum(json.loads(l).get("usd", 0) for l in LEDGER.read_text(encoding="utf-8").splitlines() if l.strip())


async def call_json(
    *,
    system: str,
    content: list[dict] | str,
    schema: dict,
    tag: str,
    model: str | None = None,
    effort: str = "high",
    max_tokens: int = 64000,
    use_cache: bool = True,
) -> dict:
    """One structured call. Returns the parsed JSON object. Cached on disk by the full request.

    max_tokens is not part of the key (that would invalidate every existing entry); instead the entry records the limit
    it was produced under and is ignored when a smaller limit is requested (truncated outputs are never cached)."""
    model = model or MODEL
    if isinstance(content, str):
        content = [{"type": "text", "text": content}]
    payload = {"model": model, "system": system, "content": content, "schema": schema, "effort": effort}
    key = _key(payload)
    cache_file = paths.CACHE / key[:2] / f"{key}.json"
    if use_cache and cache_file.exists():
        hit = json.loads(cache_file.read_text(encoding="utf-8"))
        if max_tokens >= hit.get("max_tokens", 0):
            return hit["result"]

    kwargs = dict(
        model=model,
        max_tokens=max_tokens,
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": content}],
        output_config={"effort": effort, "format": {"type": "json_schema", "schema": schema}},
    )
    b = budget()
    async with _semaphore():
        # checked inside the semaphore: at most MAX_CONCURRENCY calls can pass against the same stale spend
        if b.spent > b.cap:
            raise LLMError(f"run budget exhausted (${b.spent:.2f} > MAX_RUN_USD={b.cap})")
        t0 = time.time()
        msg = await _stream(kwargs)
        dt = time.time() - t0
    returned = getattr(msg, "model", None) or model  # the model that actually answered (fallbacks can differ)
    usd = cost(returned if returned in PRICES else model, msg.usage)
    b.add(usd)
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.time(), "tag": tag, "model": model, "model_returned": returned,
                            "usd": round(usd, 5), "sec": round(dt, 1),
                            "in": msg.usage.input_tokens, "out": msg.usage.output_tokens,
                            "cache_read": getattr(msg.usage, "cache_read_input_tokens", 0),
                            "stop": msg.stop_reason}) + "\n")
    if msg.stop_reason == "max_tokens":
        raise Truncated(f"{tag}: output truncated at max_tokens={max_tokens}")
    if msg.stop_reason == "refusal":
        raise LLMError(f"{tag}: refusal {getattr(msg, 'stop_details', None)}")
    text = next((b.text for b in msg.content if b.type == "text"), None)
    if text is None:
        raise LLMError(f"{tag}: no text block (stop={msg.stop_reason})")
    result = json.loads(text)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps({"tag": tag, "max_tokens": max_tokens, "model_returned": returned,
                                      "result": result}, ensure_ascii=False), encoding="utf-8")
    return result


async def _stream(kwargs: dict):
    global USE_FALLBACKS
    if USE_FALLBACKS:
        try:
            async with client().beta.messages.stream(
                **kwargs, betas=["server-side-fallback-2026-07-01"], fallbacks="default"
            ) as stream:
                return await stream.get_final_message()
        except (anthropic.BadRequestError, TypeError) as exc:
            if "fallback" not in str(exc).lower():
                raise
            USE_FALLBACKS = False  # account/SDK doesn't support it: plain requests from now on
    async with client().messages.stream(**kwargs) as stream:
        return await stream.get_final_message()


def run(coro):
    """Run a coroutine from sync code (CLI / worker thread) with its own spend budget."""
    token = _budget.set(Budget(MAX_RUN_USD))
    try:
        return asyncio.run(coro)
    finally:
        _budget.reset(token)
