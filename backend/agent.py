"""Campus Customs shop agent: wiring for prompt + model + tools."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from functools import lru_cache
from pathlib import Path

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.exceptions import UnexpectedModelBehavior, UsageLimitExceeded
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, ToolReturnPart, UserPromptPart
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.usage import UsageLimits

import audit
from models import MAX_HISTORY_TURNS, AgentReply, ChatResponse, ChatTurn, ShopDeps
from tools import AGENT_TOOLS, build_results

HERE = Path(__file__).resolve().parent
PROMPT_PATH = HERE / "prompts" / "prompt.md"
MODEL_NAME = "gpt-5.6-luna"
PORTKEY_BASE_URL = "https://api.portkey.ai/v1"

# ---- Thinking time limit (Problem 9) ----
# Hard wall-clock limit for one chat reply; override with AGENT_TIMEOUT_SECONDS in .env.
AGENT_TIMEOUT_SECONDS = float(os.getenv("AGENT_TIMEOUT_SECONDS", "25"))
# Stops runaway loops: at most 6 model calls and 10 tool calls per shopper message.
USAGE_LIMITS = UsageLimits(request_limit=6, tool_calls_limit=10)

TIMEOUT_REPLY = (
    "Sorry, that one took me too long to look up! Could you try asking in a simpler way, "
    'like "Is the Yale Dad Hoodie in stock in M?" You can also browse everything on the Products page.'
)
TOO_COMPLEX_REPLY = (
    "That question needed more lookups than I can do at once. Could you ask about one or two items at a time? "
    "For example: \"What crewnecks do you have in navy?\""
)

UNVERIFIED_REPLY = (
    "I want to be sure I give you exact prices and stock, and I couldn't double-check the numbers just now. "
    "Please open the product page to see live prices and sizes, or ask me again about one item."
)

log = logging.getLogger("campus_customs.agent")

# ---------- Safety rule: never invent numbers (Problem 12) ----------
# Every $ amount and stock/count number in a reply must appear in this turn's tool results
# (or in the shopper's own message / the page context). Otherwise the agent must retry.
DOLLARS_RE = re.compile(r"\$\s?(\d{1,4}(?:,\d{3})*(?:\.\d{1,2})?)")
QUANTITY_RES = [
    re.compile(r"\b(\d{1,4})\s+(?:left|available|in stock|remaining)\b", re.I),
    re.compile(r"\b(?:XXL|XL|XS|S|M|L)\s*\((\d{1,4})\)"),
    re.compile(r"\bonly\s+(\d{1,4})\b", re.I),
    re.compile(r"\b(?:have|found|carry|stock)\s+(\d{1,4})\b", re.I),
]
NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")


def _as_text(value) -> str:
    return json.dumps(value, default=lambda o: o.model_dump() if hasattr(o, "model_dump") else str(o))


def _numbers(text: str) -> set[float]:
    return {float(n) for n in NUMBER_RE.findall(text.replace(",", ""))}


def claimed_numbers(reply: str) -> list[tuple[str, float]]:
    found = [("$" + m, float(m.replace(",", ""))) for m in DOLLARS_RE.findall(reply)]
    for rx in QUANTITY_RES:
        found += [(m, float(m)) for m in rx.findall(reply)]
    return found


def unverified_numbers(reply: str, messages: list[ModelMessage], deps: ShopDeps) -> list[str]:
    """Numbers in the reply that don't appear in this turn's tool results, the shopper's message, or page context."""
    start = 0  # this turn = everything after the last shopper message
    for i, m in enumerate(messages):
        if isinstance(m, ModelRequest) and any(isinstance(p, UserPromptPart) for p in m.parts):
            start = i
    allowed: set[float] = set()
    for m in messages[start:]:
        for p in getattr(m, "parts", []):
            if isinstance(p, ToolReturnPart):
                allowed |= _numbers(_as_text(p.content))
            elif isinstance(p, UserPromptPart):
                allowed |= _numbers(str(p.content))
    for prod in [deps.page.current_product, *deps.page.cards_on_screen]:
        if prod:
            allowed.add(float(prod.price))
    return list(dict.fromkeys(label for label, value in claimed_numbers(reply) if value not in allowed))


def load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8").strip()


def build_model() -> OpenAIResponsesModel:
    api_key = os.getenv("PORTKEY_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("PORTKEY_API_KEY is missing; expected it in the workspace .env file")
    return OpenAIResponsesModel(MODEL_NAME, provider=OpenAIProvider(base_url=PORTKEY_BASE_URL, api_key=api_key))


@lru_cache(maxsize=1)
def get_agent() -> Agent[ShopDeps, AgentReply]:
    """Build the agent once (lazily, after .env is loaded) and reuse it for every request."""
    agent = Agent(
        build_model(),
        deps_type=ShopDeps,
        output_type=AgentReply,
        instructions=load_prompt(),
        tools=AGENT_TOOLS,
        retries=2,
    )

    @agent.instructions
    def shopper_and_page_context(ctx: RunContext[ShopDeps]) -> str:
        """Code-generated context added to the prompt on every run, from the request's deps."""
        return describe_context(ctx.deps)

    @agent.output_validator
    def check_numbers(ctx: RunContext[ShopDeps], output: AgentReply) -> AgentReply:
        """Safety rule "never invent numbers": reject replies with prices/quantities not backed by a tool result."""
        bad = unverified_numbers(output.reply, ctx.messages, ctx.deps)
        if bad:
            audit.append({
                "run_id": audit.current_run_id.get(), "event": "safety", "rule": "never_invent_numbers",
                "action": "retry", "detail": f"unverified in reply: {', '.join(bad)}",
            })
            raise ModelRetry(
                f"Your reply mentions {', '.join(bad)}, which did not come from any tool result in this turn. "
                "Only state prices, quantities and counts returned by get_price / get_stock / search_products / "
                "find_alternatives in this turn. Call the tool if needed, or leave the number out."
            )
        return output

    return agent


def describe_context(deps: ShopDeps) -> str:
    shopper, page = deps.shopper, deps.page
    lines = ["## Current context (generated by the website for this message)"]
    if shopper.logged_in:
        lines.append(
            f"- Shopper: {shopper.full_name} (first name {shopper.first_name}), email {shopper.email}, "
            f"member since {shopper.member_since}. They are logged in and their chat history is saved."
        )
    else:
        lines.append("- Shopper: a guest (not logged in). You don't know their name or email.")

    where = {
        "home": "the Home page",
        "products": "the Products page",
        "product_detail": "a single-item product page",
        "about": "the About us page",
        "account": "a login / create-account page",
    }.get(page.page_type, f"the page {page.path}")
    lines.append(f"- Page: {where} ({page.path})" + (f", filtered by {page.listing_filter}" if page.listing_filter else "") + ".")

    if page.current_product:
        p = page.current_product
        lines.append(
            f'- Product open on screen: "{p.name}" (product_id: {p.product_id}, {p.garment_type}, '
            f"colors: {', '.join(p.colors)}, ${p.price:.2f}). If the shopper says \"this\", \"it\" or "
            "\"this one\" without naming an item, they mean this product."
        )
    if page.cards_on_screen:
        listed = "; ".join(f"{i}. {c.name} ({c.product_id})" for i, c in enumerate(page.cards_on_screen, 1))
        lines.append(f"- Chat result cards on screen, in order: {listed}. \"The second one\" etc. refers to this order.")
    lines.append("- Still call get_price / get_stock for price and stock; the context above is only for knowing which item.")
    return "\n".join(lines)


def to_message_history(history: list[ChatTurn]) -> list[ModelMessage]:
    """Convert the widget's chat history into PydanticAI messages (last few turns only)."""
    messages: list[ModelMessage] = []
    for turn in history[-MAX_HISTORY_TURNS:]:
        if turn.role == "user":
            messages.append(ModelRequest(parts=[UserPromptPart(content=turn.content)]))
        else:
            messages.append(ModelResponse(parts=[TextPart(content=turn.content)]))
    return messages


def _end(run_id: str, started: float, stop_reason: str, usage=None, **extra) -> float:
    seconds = round(time.monotonic() - started, 1)
    entry = {"run_id": run_id, "event": "run_end", "stop_reason": stop_reason, "seconds": seconds}
    if usage is not None:
        entry |= {
            "model_requests": usage.requests,
            "tool_calls": getattr(usage, "tool_calls", None),
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
        }
    audit.append(entry | extra)
    return seconds


async def run_chat(message: str, history: list[ChatTurn], deps: ShopDeps) -> ChatResponse:
    """Run one agent turn with a time limit and step limits, so the chat never hangs.

    Every run is audited: run_start, each tool_call, any safety event, and run_end with its stop reason.
    """
    started = time.monotonic()
    run_id = audit.new_run_id()
    token = audit.current_run_id.set(run_id)
    audit.append({
        "run_id": run_id, "event": "run_start", "model": MODEL_NAME,
        "shopper": audit.mask_email(deps.shopper.email) if deps.shopper.logged_in and deps.shopper.email else "guest",
        "page": deps.page.path, "message": audit.short(message, 120), "history_turns": len(history),
    })
    try:
        result = await asyncio.wait_for(
            get_agent().run(
                message, deps=deps, message_history=to_message_history(history), usage_limits=USAGE_LIMITS
            ),
            timeout=AGENT_TIMEOUT_SECONDS,
        )
    except TimeoutError:
        log.warning("Agent timed out after %.0fs: %r", AGENT_TIMEOUT_SECONDS, message[:80])
        seconds = _end(run_id, started, "timeout", limit_seconds=AGENT_TIMEOUT_SECONDS)
        return ChatResponse(reply=TIMEOUT_REPLY, status="timeout", seconds=seconds)
    except UsageLimitExceeded as exc:
        log.warning("Agent hit usage limit (%s): %r", exc, message[:80])
        seconds = _end(run_id, started, "usage_limit", detail=audit.short(str(exc), 120))
        return ChatResponse(reply=TOO_COMPLEX_REPLY, status="too_complex", seconds=seconds)
    except UnexpectedModelBehavior as exc:
        # Raised when the reply kept failing the number check after its retries.
        log.warning("Agent output rejected (%s): %r", exc, message[:80])
        seconds = _end(run_id, started, "unverified_numbers", detail=audit.short(str(exc), 120))
        return ChatResponse(reply=UNVERIFIED_REPLY, status="unverified", seconds=seconds)
    except Exception as exc:
        _end(run_id, started, "error", detail=audit.short(f"{type(exc).__name__}: {exc}", 120))
        raise
    finally:
        audit.current_run_id.reset(token)
    reply: AgentReply = result.output
    # Cards are rebuilt from the database, so prices/stock on the page are always real.
    results = build_results(reply.results_title, reply.picks, reply.total_matches)
    seconds = _end(
        run_id, started, "final_answer", result.usage() if callable(result.usage) else result.usage,
        reply=audit.short(reply.reply, 120), cards=len(results.products) if results else 0,
    )
    return ChatResponse(reply=reply.reply, results=results, seconds=seconds)
