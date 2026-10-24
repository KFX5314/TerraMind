"""Thin Claude wrapper: JSON-schema outputs, disk cache keyed by request hash, usage/cost ledger, concurrency cap."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import os
import time
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

_client: anthropic.AsyncAnthropic | None = None
_sem: asyncio.Semaphore | None = None
_spent = 0.0


class LLMError(RuntimeError):
    pass


class Truncated(LLMError):
    pass


def client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(max_retries=6, timeout=900)
    return _client


def _semaphore() -> asyncio.Semaphore:
    global _sem
    if _sem is None:
        _sem = asyncio.Semaphore(MAX_CONCURRENCY)
    return _sem


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
    """One structured call. Returns the parsed JSON object. Cached on disk by the full request."""
    global _spent
    model = model or MODEL
    if isinstance(content, str):
        content = [{"type": "text", "text": content}]
    payload = {"model": model, "system": system, "content": content, "schema": schema, "effort": effort}
    key = _key(payload)
    cache_file = paths.CACHE / key[:2] / f"{key}.json"
    if use_cache and cache_file.exists():
        return json.loads(cache_file.read_text(encoding="utf-8"))["result"]
    if _spent > MAX_RUN_USD:
        raise LLMError(f"run budget exhausted (${_spent:.2f} > MAX_RUN_USD={MAX_RUN_USD})")

    kwargs = dict(
        model=model,
        max_tokens=max_tokens,
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": content}],
        output_config={"effort": effort, "format": {"type": "json_schema", "schema": schema}},
    )
    async with _semaphore():
        t0 = time.time()
        msg = await _stream(kwargs)
        dt = time.time() - t0
    usd = cost(model, msg.usage)
    _spent += usd
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.time(), "tag": tag, "model": model, "usd": round(usd, 5), "sec": round(dt, 1),
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
    cache_file.write_text(json.dumps({"tag": tag, "result": result}, ensure_ascii=False), encoding="utf-8")
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
    """Run a coroutine from sync code (CLI / worker thread). Client and semaphore are loop-bound: reset per run."""
    global _client, _sem
    _client, _sem = None, None
    return asyncio.run(coro)
