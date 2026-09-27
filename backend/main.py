"""Campus Customs API.

Problem 3: serves the product catalogue, per-size inventory, and product images.
Problem 4: create-account / login with hashed passwords (see auth.py, security.py).
Problem 5: /api/chat runs the PydanticAI shop agent (agent.py, tools.py, models.py, prompts/prompt.md).
Problem 8: saved chat history for logged-in shoppers (chat_history.py) and shopper/page context (context.py).

Run from the backend/ folder:  uvicorn main:app --reload --port 8000
"""

import json
import logging
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

# Load secrets before importing modules that read them (HW4/.env, then the workspace-root .env).
HW4_DIR = Path(__file__).resolve().parent.parent
load_dotenv(HW4_DIR / ".env")
load_dotenv(HW4_DIR.parent / ".env")

from fastapi import Cookie, FastAPI, HTTPException, Request  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

import audit  # noqa: E402
from agent import run_chat  # noqa: E402
from security import LoginRateLimiter  # noqa: E402
from auth import get_current_user  # noqa: E402
from auth import router as auth_router  # noqa: E402
from db import DATA_DIR, get_db  # noqa: E402
from chat_history import load_agent_history, load_saved_messages, save_exchange  # noqa: E402
from context import build_deps  # noqa: E402
from models import ChatHistory, ChatRequest, ChatResponse  # noqa: E402

log = logging.getLogger("campus_customs")

app = FastAPI(title="Campus Customs API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Product images: catalogue.image_file_path "products/x.jpg" -> /media/products/x.jpg
# Only the products folder is mounted so the .db file is never downloadable.
app.mount("/media/products", StaticFiles(directory=DATA_DIR / "products"), name="media")

app.include_router(auth_router)


def product_from_row(row: sqlite3.Row) -> dict:
    image_path = row["image_file_path"]
    return {
        "product_id": row["product_id"],
        "name": row["name"],
        "garment_type": row["garment_type"],
        "description": row["description"],
        "colors": json.loads(row["colors"]),
        "search_tags": json.loads(row["search_tags"]),
        "image_file_path": image_path,
        "image_url": "/media/" + image_path,
        "price": row["price"],
    }


SIZE_ORDER = "CASE size WHEN 'XS' THEN 0 WHEN 'S' THEN 1 WHEN 'M' THEN 2 WHEN 'L' THEN 3 WHEN 'XL' THEN 4 WHEN 'XXL' THEN 5 ELSE 6 END"


def inventory_for(conn: sqlite3.Connection, product_id: str) -> list[dict]:
    rows = conn.execute(
        f"SELECT size, quantity FROM inventory WHERE product_id = ? ORDER BY {SIZE_ORDER}",
        (product_id,),
    ).fetchall()
    return [{"size": r["size"], "quantity": r["quantity"]} for r in rows]


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/products")
def list_products(q: str | None = None) -> list[dict]:
    """All products with stock by size, optionally filtered by a keyword across name, type, description, colors and tags."""
    sql = "SELECT * FROM catalogue"
    params: list[str] = []
    if q:
        like = f"%{q.lower()}%"
        sql += (
            " WHERE lower(name) LIKE ? OR lower(garment_type) LIKE ? OR lower(description) LIKE ?"
            " OR lower(colors) LIKE ? OR lower(search_tags) LIKE ?"
        )
        params = [like] * 5
    sql += " ORDER BY name"
    with get_db() as conn:
        products = [product_from_row(r) for r in conn.execute(sql, params).fetchall()]
        # Stock by size for every product in one query (used by the size filter, sort, and card stock line).
        stock: dict[str, list[dict]] = {}
        for r in conn.execute(f"SELECT product_id, size, quantity FROM inventory ORDER BY product_id, {SIZE_ORDER}"):
            stock.setdefault(r["product_id"], []).append({"size": r["size"], "quantity": r["quantity"]})
    for p in products:
        p["inventory"] = stock.get(p["product_id"], [])
        p["total_stock"] = sum(i["quantity"] for i in p["inventory"])
    return products


@app.get("/api/products/{product_id}")
def get_product(product_id: str) -> dict:
    """One product with its stock by size."""
    with get_db() as conn:
        row = conn.execute("SELECT * FROM catalogue WHERE product_id = ?", (product_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Product not found")
        product = product_from_row(row)
        product["inventory"] = inventory_for(conn, product_id)
        product["total_stock"] = sum(i["quantity"] for i in product["inventory"])
        return product


# ---------- Chat (PydanticAI agent) ----------


# Safety rule "abuse & cost limits": at most 15 chat messages per minute per shopper (or per IP for guests).
CHAT_RATE_LIMIT = 15
chat_limiter = LoginRateLimiter(max_failures=CHAT_RATE_LIMIT, window_seconds=60)


@app.post("/api/chat")
async def chat(body: ChatRequest, request: Request, cc_session: str | None = Cookie(default=None)) -> ChatResponse:
    """Send one shopper message to the agent; returns its reply and product cards.

    Logged in: conversation memory is loaded from chat_messages, and the exchange is saved there.
    Guest: the browser's history is used and nothing is saved.
    """
    user = get_current_user(cc_session)
    # Safety rule "protect personal data": strip card numbers before the model, database or audit log see them.
    message = audit.redact_card_numbers(body.message.strip())
    who = f"user:{user.id}" if user else f"ip:{request.client.host if request.client else 'unknown'}"
    if chat_limiter.is_blocked(who):
        audit.append({
            "run_id": None, "event": "safety", "rule": "abuse_cost_limits", "action": "blocked",
            "detail": f"more than {CHAT_RATE_LIMIT} messages/minute", "stop_reason": "rate_limited",
            "shopper": audit.mask_email(user.email) if user else "guest",
        })
        raise HTTPException(
            status_code=429, detail="You're sending messages quickly! Please wait a moment and try again."
        )
    chat_limiter.record_failure(who)  # counts every message toward the per-minute limit
    deps = build_deps(user, body.page)
    history = load_agent_history(user.id) if user else body.history
    try:
        response = await run_chat(message, history, deps)
    except Exception:
        log.exception("Agent run failed")
        raise HTTPException(status_code=502, detail="Our assistant is having trouble right now. Please try again.")
    # Only complete answers are saved; a timed-out attempt shouldn't clutter the shopper's history.
    if user and response.status == "ok":
        save_exchange(user.id, message, response)
    return response


@app.get("/api/chat/history")
def chat_history(cc_session: str | None = Cookie(default=None)) -> ChatHistory:
    """The logged-in shopper's saved chat (most recent 50 messages). Guests get an empty history."""
    user = get_current_user(cc_session)
    if user is None:
        return ChatHistory(logged_in=False)
    return ChatHistory(logged_in=True, messages=load_saved_messages(user.id))
