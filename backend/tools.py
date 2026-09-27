"""Tools the Campus Customs agent can call.

Every tool is read-only and only touches the `catalogue` and `inventory` tables.
The agent has no tool that can see `users` or `password_hash`.
"""

from __future__ import annotations

import json
import re
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from pydantic_ai import RunContext

from audit import audited_tool
from db import DB_PATH
from models import (
    LOW_STOCK_THRESHOLD,
    AlternativeItem,
    AlternativesResult,
    PriceInfo,
    ProductCard,
    ProductDescription,
    ProductInfo,
    ProductMatch,
    ProductNotFound,
    ProductSummary,
    SearchResults,
    SizeStatus,
    SizeStock,
    StockReport,
)
from models import MAX_CARDS, CardPick, ChatResults, PageInfo, ShopDeps, ShopperProfile

SIZES = ["XS", "S", "M", "L", "XL", "XXL"]
SIZE_ORDER = "CASE size WHEN 'XS' THEN 0 WHEN 'S' THEN 1 WHEN 'M' THEN 2 WHEN 'L' THEN 3 WHEN 'XL' THEN 4 WHEN 'XXL' THEN 5 ELSE 6 END"
STOPWORDS = {
    "a", "an", "and", "any", "are", "do", "for", "have", "i", "in", "is", "me", "my", "of", "on", "or", "show",
    "some", "the", "to", "want", "with", "you", "your", "what", "looking", "something", "got", "need", "yale",
}


CATEGORY_WORDS = {
    "hoodie": "hoodie", "hoodies": "hoodie", "hoody": "hoodie", "hood": "hoodie",
    "crewneck": "crewneck", "crewnecks": "crewneck",
    "tee": "t-shirt", "tees": "t-shirt", "tshirt": "t-shirt", "tshirts": "t-shirt", "shirt": "t-shirt", "shirts": "t-shirt",
    "jacket": "jacket", "jackets": "jacket",
    "fleece": "fleece",
}


@contextmanager
def read_only_db() -> Iterator[sqlite3.Connection]:
    """Open the database in read-only mode so no tool can ever change data."""
    conn = sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def _inventory(conn: sqlite3.Connection, product_id: str) -> list[SizeStock]:
    rows = conn.execute(
        f"SELECT size, quantity FROM inventory WHERE product_id = ? ORDER BY {SIZE_ORDER}", (product_id,)
    ).fetchall()
    return [SizeStock(size=r["size"], quantity=r["quantity"]) for r in rows]


def _info(conn: sqlite3.Connection, row: sqlite3.Row) -> ProductInfo:
    inventory = _inventory(conn, row["product_id"])
    return ProductInfo(
        product_id=row["product_id"],
        name=row["name"],
        garment_type=row["garment_type"],
        colors=json.loads(row["colors"]),
        price=row["price"],
        total_stock=sum(s.quantity for s in inventory),
        sizes_in_stock=[s.size for s in inventory if s.quantity > 0],
        description=row["description"],
        search_tags=json.loads(row["search_tags"]),
        inventory=inventory,
    )


def _normalize_size(size: str) -> str:
    s = size.strip().upper().replace("EXTRA ", "X").replace("-", "")
    return {"SMALL": "S", "MEDIUM": "M", "LARGE": "L", "XLARGE": "XL", "XXLARGE": "XXL", "2XL": "XXL"}.get(s, s)


# ---------- Agent tools ----------


def search_products(
    query: str = "",
    garment_type: str | None = None,
    color: str | None = None,
    max_price: float | None = None,
    size: str | None = None,
    limit: int = 12,
) -> SearchResults:
    """Search the Campus Customs catalogue.

    Args:
        query: Keywords from the shopper, e.g. "hockey", "Pierson college", "grandpa gift", "vintage bulldog".
        garment_type: Optional kind of item, e.g. "hoodie", "crewneck", "t-shirt", "quarter-zip", "jacket".
        color: Optional color, e.g. "navy", "gray", "white".
        max_price: Optional maximum price in USD.
        size: Optional size (XS, S, M, L, XL, XXL). Each result then includes requested_size_quantity
            (0 = sold out in that size); items in stock in that size are listed first.
        limit: Maximum number of results to return (1-12). Use 12 for "what X do you have?" browsing questions.

    Returns total_matches (how many items match in all) and the best matches, each with price,
    colors, and sizes in stock. total_matches = 0 means nothing in the catalogue matches.
    """
    limit = max(1, min(limit, 12))
    words = [w for w in re.findall(r"[a-z0-9]+", query.lower()) if w not in STOPWORDS and len(w) > 1]
    # A category word in the query ("hoodies", "tees", "jackets"...) acts as the garment filter, so
    # "what hoodies do you have?" counts every hoodie, not just items whose text contains "hoodie".
    if not garment_type:
        for w in list(words):
            if w in CATEGORY_WORDS:
                garment_type = CATEGORY_WORDS[w]
                words.remove(w)
                break
    wanted_size = _normalize_size(size) if size else None

    with read_only_db() as conn:
        scored: list[tuple[int, ProductInfo]] = []
        for row in conn.execute("SELECT * FROM catalogue").fetchall():
            name = row["name"].lower()
            gtype = row["garment_type"].lower()
            text = " ".join([name, gtype, row["description"].lower(), row["colors"].lower(), row["search_tags"].lower()])

            if garment_type and not _type_matches(garment_type, gtype, name):
                continue
            if color and color.lower() not in row["colors"].lower():
                continue
            if max_price is not None and row["price"] > max_price:
                continue

            score = sum(3 if w in name else 1 for w in words if w in text)
            if words and score == 0:
                continue

            scored.append((score, _info(conn, row)))

    def size_qty(info: ProductInfo) -> int | None:
        if not wanted_size:
            return None
        return next((s.quantity for s in info.inventory if s.size == wanted_size), 0)

    # Best keyword match first; when a size was asked for, in-stock items rank above sold-out ones.
    scored.sort(key=lambda s: (-s[0], (size_qty(s[1]) or 0) == 0 if wanted_size else False, s[1].name))
    results = []
    for _, info in scored[:limit]:
        summary = ProductSummary(**info.model_dump(include=set(ProductSummary.model_fields)))
        summary.requested_size_quantity = size_qty(info)
        results.append(summary)
    prices = [info.price for _, info in scored]
    return SearchResults(
        total_matches=len(scored),
        price_min=min(prices) if prices else None,
        price_max=max(prices) if prices else None,
        products=results,
    )


def _type_matches(wanted: str, garment_type: str, name: str) -> bool:
    w = wanted.lower().replace("sweatshirt", "").strip()
    aliases = {
        "hoodie": ["hood"],
        "hoodies": ["hood"],
        "crewneck": ["crewneck", "crew"],
        "tee": ["t-shirt", "t shirt"],
        "t-shirt": ["t-shirt", "t shirt"],
        "tshirt": ["t-shirt", "t shirt"],
        "shirt": ["shirt"],
        "quarter-zip": ["quarter-zip", "1 4 zip"],
        "quarter zip": ["quarter-zip", "1 4 zip"],
        "jacket": ["jacket"],
        "fleece": ["fleece"],
    }
    keys = aliases.get(w, [w])
    return any(k in garment_type or k in name for k in keys)


def _slug(text: str) -> str:
    return "-".join(re.findall(r"[a-z0-9]+", text.lower()))


def _resolve_product(conn: sqlite3.Connection, product: str) -> sqlite3.Row | ProductNotFound:
    """Find exactly one catalogue row by product_id or product name; never guess between several."""
    row = conn.execute("SELECT * FROM catalogue WHERE product_id = ?", (product.strip(),)).fetchone()
    if row is None:
        slug = _slug(product)
        row = conn.execute(
            "SELECT * FROM catalogue WHERE product_id = ? OR lower(name) = ?", (slug, product.strip().lower())
        ).fetchone()
    if row is not None:
        return row
    suggestions = [ProductMatch(product_id=p.product_id, name=p.name) for p in search_products(product, limit=5).products]
    return ProductNotFound(
        query=product,
        message=(
            f"No product exactly matches '{product}'. Retry with one of the suggested product_ids."
            if suggestions
            else f"Campus Customs does not carry anything matching '{product}'."
        ),
        suggestions=suggestions,
    )


def _size_status(size: str, quantity: int) -> SizeStatus:
    status = "sold_out" if quantity == 0 else "low_stock" if quantity <= LOW_STOCK_THRESHOLD else "in_stock"
    return SizeStatus(size=size, quantity=quantity, status=status)


def get_product_description(product: str) -> ProductDescription | ProductNotFound:
    """Look up a product's description, garment type, and available colors in the database.

    Use for "tell me about…", "what does it look like?", "what colors does it come in?".

    Args:
        product: The product_id from search_products (preferred), or the exact product name.
    """
    with read_only_db() as conn:
        row = _resolve_product(conn, product)
    if isinstance(row, ProductNotFound):
        return row
    return ProductDescription(
        product_id=row["product_id"],
        name=row["name"],
        garment_type=row["garment_type"],
        description=row["description"],
        colors=json.loads(row["colors"]),
        search_tags=json.loads(row["search_tags"]),
    )


def get_price(product: str) -> PriceInfo | ProductNotFound:
    """Look up the current price of a product in the database. Call this for every price question.

    Args:
        product: The product_id from search_products (preferred), or the exact product name.
    """
    with read_only_db() as conn:
        row = _resolve_product(conn, product)
    if isinstance(row, ProductNotFound):
        return row
    return PriceInfo(product_id=row["product_id"], name=row["name"], price=row["price"], price_display=f"${row['price']:,.2f}")


def get_stock(product: str, size: str | None = None) -> StockReport | ProductNotFound:
    """Look up how many of a product are in stock, by size, in the database.

    Call this for every stock / availability / "do you have it in size…" question.

    Args:
        product: The product_id from search_products (preferred), or the exact product name.
        size: Optional size the shopper asked about: XS, S, M, L, XL or XXL ("medium", "large", "2XL" also work).
    """
    with read_only_db() as conn:
        row = _resolve_product(conn, product)
        if isinstance(row, ProductNotFound):
            return row
        sizes = [_size_status(s.size, s.quantity) for s in _inventory(conn, row["product_id"])]

    name = row["name"]
    in_stock = [s.size for s in sizes if s.quantity > 0]
    sold_out = [s.size for s in sizes if s.quantity == 0]
    total = sum(s.quantity for s in sizes)
    available = ", ".join(f"{s.size} ({s.quantity})" for s in sizes if s.quantity > 0) or "none"

    wanted = _normalize_size(size) if size else None
    requested = next((s for s in sizes if s.size == wanted), None) if wanted else None

    if wanted and requested is None:
        summary = f"We don't carry size '{size}'. Sizes are {', '.join(SIZES)}. {name} in stock: {available}."
    elif requested and requested.status == "sold_out":
        summary = f"{name} is SOLD OUT in size {requested.size} (0 left). Sizes in stock: {available}."
    elif requested:
        few = " (only a few left)" if requested.status == "low_stock" else ""
        summary = f"{name} is in stock in size {requested.size}: {requested.quantity} left{few}."
    elif total == 0:
        summary = f"{name} is SOLD OUT in every size."
    else:
        sold = f" Sold out: {', '.join(sold_out)}." if sold_out else ""
        summary = f"{name} has {total} in stock. By size: {available}.{sold}"

    return StockReport(
        product_id=row["product_id"],
        name=name,
        requested_size=wanted,
        requested_size_status=requested,
        sizes=sizes,
        sizes_in_stock=in_stock,
        sizes_sold_out=sold_out,
        total_in_stock=total,
        summary=summary,
    )


# ---------- Sold-out alternatives (Problem 9) ----------

GARMENT_FAMILIES = {
    "hoodie": ("hood",),
    "crewneck": ("crewneck", "crew-neck sweatshirt", "mockneck"),
    "t-shirt": ("t-shirt", "t shirt", "tee", "performance shirt"),
    "quarter-zip": ("quarter-zip", "1 4 zip"),
    "jacket": ("jacket", "fleece"),
}
THEME_STOPWORDS = STOPWORDS | {
    "sweatshirt", "shirt", "long", "sleeve", "short", "logo", "college", "apparel", "merch", "campus", "customs",
    "university", "pullover", "navy", "white", "gray", "grey", "heather", "blue", "hoodie", "crewneck", "chest",
    "drawstring", "hood", "hooded", "kangaroo", "pocket", "crew", "neck", "full", "zip", "quarter", "jacket",
    "graphic", "sweater", "fleece", "ribbed", "cuffs", "tee", "lettering", "wordmark", "print", "charcoal", "black",
    "spirit", "school", "sports", "sport", "vintage", "classic", "casual", "style", "zipper", "sleeves",
}


def _family(garment_type: str, name: str) -> str | None:
    text = f"{garment_type} {name}".lower()
    for family, keys in GARMENT_FAMILIES.items():
        if any(k in text for k in keys):
            return family
    return None


def _theme_words(row: sqlite3.Row) -> set[str]:
    words = set(re.findall(r"[a-z]+", (row["name"] + " " + row["search_tags"]).lower()))
    return {w for w in words if len(w) > 2 and w not in THEME_STOPWORDS}


def find_alternatives(product: str, size: str, limit: int = 4) -> AlternativesResult | ProductNotFound | str:
    """Find similar items that ARE in stock in the shopper's size. Use this whenever an item is sold out
    (or has none left) in the size the shopper wants, so you can offer a replacement instead of a dead end.

    Similarity: same kind of garment first, then shared colors, shared theme (sport, college, relative,
    bulldog...), and a close price.

    Args:
        product: The sold-out item's product_id (preferred) or exact name.
        size: The size the shopper needs: XS, S, M, L, XL or XXL.
        limit: How many alternatives to return (1-6).
    """
    wanted = _normalize_size(size)
    if wanted not in SIZES:
        return f"'{size}' is not a size we carry. Sizes are: {', '.join(SIZES)}."
    limit = max(1, min(limit, 6))

    with read_only_db() as conn:
        original = _resolve_product(conn, product)
        if isinstance(original, ProductNotFound):
            return original
        orig_qty = conn.execute(
            "SELECT quantity FROM inventory WHERE product_id = ? AND size = ?", (original["product_id"], wanted)
        ).fetchone()["quantity"]
        orig_family = _family(original["garment_type"], original["name"])
        orig_colors = set(json.loads(original["colors"]))
        orig_theme = _theme_words(original)

        candidates = conn.execute(
            "SELECT c.*, i.quantity AS qty FROM catalogue c JOIN inventory i ON i.product_id = c.product_id"
            " WHERE i.size = ? AND i.quantity > 0 AND c.product_id != ?",
            (wanted, original["product_id"]),
        ).fetchall()

    scored: list[tuple[float, AlternativeItem]] = []
    for row in candidates:
        colors = json.loads(row["colors"])
        why: list[str] = []
        score = 0.0
        family = _family(row["garment_type"], row["name"])
        if orig_family and family == orig_family:
            score += 10
            why.append(f"same kind: {orig_family}")
        shared_colors = [c for c in colors if c in orig_colors]
        if shared_colors:
            score += 2 * min(len(shared_colors), 2)
            why.append("shares color: " + ", ".join(shared_colors[:2]))
        shared_theme = sorted(orig_theme & _theme_words(row))
        if shared_theme:
            # A shared subject (hockey, Pierson, bulldog, dad...) counts more than a shared layout (left-chest logo).
            score += sum(2 if w == "left" else 5 for w in shared_theme[:3])
            labels = ["left-chest logo" if w == "left" else w for w in shared_theme[:3]]
            why.append("similar theme: " + ", ".join(labels))
        price_gap = abs(row["price"] - original["price"])
        score += max(0.0, 3 - price_gap / 10)
        if price_gap == 0:
            why.append("same price")
        if score <= 3:  # nothing in common beyond price
            continue
        scored.append(
            (
                score,
                AlternativeItem(
                    product_id=row["product_id"],
                    name=row["name"],
                    garment_type=row["garment_type"],
                    colors=colors,
                    price=row["price"],
                    price_display=f"${row['price']:,.2f}",
                    quantity_in_size=row["qty"],
                    why_similar=why,
                ),
            )
        )

    scored.sort(key=lambda s: (-s[0], s[1].name))
    alts = [a for _, a in scored[:limit]]
    status = "is SOLD OUT" if orig_qty == 0 else f"has {orig_qty} left"
    summary = (
        f"{original['name']} {status} in size {wanted}. "
        + (
            "In-stock alternatives in " + wanted + ": " + "; ".join(f"{a.name} ({a.price_display}, {a.quantity_in_size} left)" for a in alts) + "."
            if alts
            else f"No similar items are in stock in {wanted} right now."
        )
    )
    return AlternativesResult(
        original_product_id=original["product_id"],
        original_name=original["name"],
        size=wanted,
        original_quantity_in_size=orig_qty,
        alternatives=alts,
        summary=summary,
    )


# ---------- Context tools (read from the per-request deps, not the database) ----------


def get_shopper_profile(ctx: RunContext[ShopDeps]) -> ShopperProfile:
    """Who is chatting: logged_in, first/last/full name, email, and member_since.

    Guests get logged_in=false with no details. Only share these details with the shopper themself.
    """
    return ctx.deps.shopper


def get_page_context(ctx: RunContext[ShopDeps]) -> PageInfo:
    """What the shopper is looking at right now: page type, the open product (current_product),
    any Products-page filter, and the chat result cards on screen (cards_on_screen, in order).

    Use this to resolve "this", "it", "this one", "the second one", etc.
    """
    return ctx.deps.page


# Every tool the agent can call is wrapped so each call lands in output/audit_trail.json.
AGENT_TOOLS = [
    audited_tool(t)
    for t in (
        search_products,
        get_product_description,
        get_price,
        get_stock,
        find_alternatives,
        get_shopper_profile,
        get_page_context,
    )
]


# ---------- Helpers used by the API (not exposed to the agent) ----------


def build_results(title: str | None, picks: list[CardPick], total_matches: int | None) -> ChatResults | None:
    """Turn the agent's picks into cards using real database data. Unknown ids are dropped."""
    cards: list[ProductCard] = []
    seen: set[str] = set()
    with read_only_db() as conn:
        for pick in picks:
            if pick.product_id in seen or len(cards) >= MAX_CARDS:
                continue
            seen.add(pick.product_id)
            row = conn.execute("SELECT * FROM catalogue WHERE product_id = ?", (pick.product_id,)).fetchone()
            if row is None:
                continue
            info = _info(conn, row)
            cards.append(
                ProductCard(
                    product_id=info.product_id,
                    name=info.name,
                    garment_type=info.garment_type,
                    description=info.description,
                    colors=info.colors,
                    image_url="/media/" + row["image_file_path"],
                    price=info.price,
                    inventory=info.inventory,
                    total_stock=info.total_stock,
                    reason=pick.reason.strip(),
                )
            )
    if not cards:
        return None
    total = max(total_matches or 0, len(cards))
    return ChatResults(title=(title or "Matching items").strip(), total_matches=total, products=cards)
