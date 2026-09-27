"""Append-only audit trail of agent-loop activity: output/audit_trail.json.

The file is one JSON array. New entries are appended by overwriting only the closing "]",
so earlier entries are never rewritten or wiped, even across server restarts.

Each chat message produces:
  run_start  -> who (masked), page, message (short)
  tool_call  -> one per tool the agent calls: tool name, short args, short result, ms
  safety     -> a safety rule fired (number check, rate limit)
  run_end    -> stop reason, model requests, tool calls, tokens, seconds
"""

from __future__ import annotations

import functools
import json
import re
import threading
import time
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel

AUDIT_PATH = Path(__file__).resolve().parent.parent / "output" / "audit_trail.json"
_lock = threading.Lock()
MAX_TEXT = 160

# The run id of the chat message currently being handled (set in agent.run_chat).
current_run_id: ContextVar[str | None] = ContextVar("current_run_id", default=None)

EMAIL_RE = re.compile(r"([A-Za-z0-9])[A-Za-z0-9._%+-]*@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")
SECRET_KEYS = ("password", "hash", "token", "secret", "cookie", "session", "api_key", "key")


# 13-19 digits, optionally separated by spaces or dashes (credit/debit card numbers).
CARD_RE = re.compile(r"\b(?:\d[ -]?){12,18}\d\b")


def mask_email(text: str) -> str:
    """Protect personal data: t***@yale.edu instead of the full address."""
    return EMAIL_RE.sub(lambda m: f"{m.group(1)}***@{m.group(2)}", text)


def redact_card_numbers(text: str) -> str:
    """Protect personal data: card numbers typed into the chat are never sent on or stored."""
    return CARD_RE.sub("[card number removed]", text)


def short(value: Any, limit: int = MAX_TEXT) -> str:
    text = value if isinstance(value, str) else json.dumps(value, default=str, ensure_ascii=False)
    text = redact_card_numbers(mask_email(" ".join(text.split())))
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _clean_args(args: dict[str, Any]) -> dict[str, Any]:
    out = {}
    for k, v in args.items():
        if k == "ctx":
            continue
        if any(s in k.lower() for s in SECRET_KEYS):
            out[k] = "[REDACTED]"
        else:
            out[k] = short(v, 80) if isinstance(v, str) else v
    return out


def summarize_result(result: Any) -> str:
    """One short line describing a tool result, e.g. 'PriceInfo: Yale Dad Hoodie $68.00'."""
    name = type(result).__name__
    if isinstance(result, BaseModel):
        d = result.model_dump()
        if "summary" in d:
            return short(f"{name}: {d['summary']}")
        if name == "SearchResults":
            ids = [p["product_id"] for p in d["products"][:3]]
            return short(f"SearchResults: {d['total_matches']} matches, showing {len(d['products'])} (${d['price_min']}–${d['price_max']}); first: {', '.join(ids)}")
        if name == "PriceInfo":
            return short(f"PriceInfo: {d['name']} {d['price_display']}")
        if name == "ProductDescription":
            return short(f"ProductDescription: {d['name']} · colors {', '.join(d['colors'])}")
        if name == "ProductNotFound":
            return short(f"ProductNotFound: {d['message']}")
        if name == "ShopperProfile":
            return short(f"ShopperProfile: logged_in={d['logged_in']} name={d.get('first_name')} email={d.get('email')}")
        if name == "PageInfo":
            cp = (d.get("current_product") or {}).get("product_id")
            return short(f"PageInfo: {d['page_type']} {d['path']} current={cp} cards={len(d['cards_on_screen'])}")
        return short(f"{name}: {d}")
    return short(f"{name}: {result}")


def append(entry: dict[str, Any]) -> None:
    """Append one entry without touching earlier ones."""
    entry = {"time": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"), **entry}
    line = json.dumps(entry, ensure_ascii=False, default=str)
    with _lock:
        AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not AUDIT_PATH.exists() or AUDIT_PATH.stat().st_size < 2:
            AUDIT_PATH.write_text("[\n" + line + "\n]\n", encoding="utf-8")
            return
        with AUDIT_PATH.open("r+b") as f:
            # Walk back from the end past whitespace to the closing "]" and overwrite just that.
            pos = f.seek(0, 2)
            while pos > 0:
                pos -= 1
                f.seek(pos)
                ch = f.read(1)
                if ch not in b" \r\n\t":
                    break
            if ch != b"]":  # not a JSON array we recognise: never destroy it, start a side file instead
                AUDIT_PATH.with_suffix(".recovered.json").write_text("[\n" + line + "\n]\n", encoding="utf-8")
                return
            # Also step back over the whitespace before "]" so the comma sits right after the last entry.
            end = pos
            while end > 0:
                f.seek(end - 1)
                if f.read(1) not in b" \r\n\t":
                    break
                end -= 1
            f.seek(end)
            f.truncate()
            f.write((",\n" + line + "\n]\n").encode("utf-8"))


def new_run_id() -> str:
    return uuid.uuid4().hex[:10]


def audited_tool(fn):
    """Wrap an agent tool so every call is written to the audit trail (works even if the run later times out)."""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        started = time.perf_counter()
        bound = {}
        try:
            import inspect

            sig = inspect.signature(fn)
            bound = dict(sig.bind_partial(*args, **kwargs).arguments)
        except TypeError:
            bound = dict(kwargs)
        try:
            result = fn(*args, **kwargs)
        except Exception as exc:
            append({
                "run_id": current_run_id.get(), "event": "tool_call", "tool": fn.__name__,
                "args": _clean_args(bound), "result": short(f"ERROR {type(exc).__name__}: {exc}"),
                "ms": round((time.perf_counter() - started) * 1000),
            })
            raise
        append({
            "run_id": current_run_id.get(), "event": "tool_call", "tool": fn.__name__,
            "args": _clean_args(bound), "result": summarize_result(result),
            "ms": round((time.perf_counter() - started) * 1000),
        })
        return result

    # tools.py uses string annotations; resolve them against the tool's own module so PydanticAI
    # builds the same tool schema for the wrapper as for the original function.
    import typing

    wrapper.__annotations__ = typing.get_type_hints(fn)
    return wrapper
