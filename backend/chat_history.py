"""Saved chat history for logged-in shoppers (table: chat_messages)."""

from __future__ import annotations

import json

from db import get_db
from models import MAX_HISTORY_TURNS, MAX_SAVED_HISTORY, CardPick, ChatResponse, ChatResults, ChatTurn, SavedMessage
from tools import build_results


def save_exchange(user_id: int, message: str, response: ChatResponse) -> None:
    """Store the shopper's message and the assistant's reply (with its product cards) as two rows."""
    results_json = response.results.model_dump_json() if response.results else None
    with get_db() as conn:
        conn.execute("INSERT INTO chat_messages (user_id, role, content) VALUES (?, 'user', ?)", (user_id, message))
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json) VALUES (?, 'assistant', ?, ?)",
            (user_id, response.reply, results_json),
        )


def _recent_rows(user_id: int, limit: int):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, role, content, products_json, created_at FROM chat_messages"
            " WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return list(reversed(rows))


def _results_from_json(products_json: str | None) -> ChatResults | None:
    """Rebuild saved cards from the database, so reloaded cards show today's price and stock.

    Handles both the current format (a ChatResults object) and the older seed format (a list of products).
    """
    if not products_json:
        return None
    try:
        data = json.loads(products_json)
    except json.JSONDecodeError:
        return None
    if isinstance(data, list):
        title, total, products = "Matching items", None, data
    elif isinstance(data, dict):
        title, total, products = data.get("title"), data.get("total_matches"), data.get("products", [])
    else:
        return None
    picks = [
        CardPick(product_id=p["product_id"], reason=(p.get("reason") or "")[:90])
        for p in products
        if isinstance(p, dict) and p.get("product_id")
    ]
    return build_results(title, picks, total)


def load_saved_messages(user_id: int, limit: int = MAX_SAVED_HISTORY) -> list[SavedMessage]:
    """History shown in the chat widget when a logged-in shopper returns."""
    return [
        SavedMessage(
            id=r["id"],
            role=r["role"],
            content=r["content"],
            results=_results_from_json(r["products_json"]) if r["role"] == "assistant" else None,
            created_at=r["created_at"],
        )
        for r in _recent_rows(user_id, limit)
        if r["role"] in ("user", "assistant")
    ]


def load_agent_history(user_id: int, turns: int = MAX_HISTORY_TURNS) -> list[ChatTurn]:
    """Recent turns fed to the agent as conversation memory (trusted: read from our database)."""
    return [ChatTurn(role=r["role"], content=r["content"][:4000]) for r in _recent_rows(user_id, turns)]
