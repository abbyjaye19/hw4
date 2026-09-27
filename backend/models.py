"""Pydantic / PydanticAI structured types for the Campus Customs shop agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, Field

MAX_MESSAGE_CHARS = 1000
MAX_HISTORY_TURNS = 12
MAX_CARDS = 12
MAX_SAVED_HISTORY = 50  # messages returned when a logged-in shopper reloads the page


# ---------- Catalogue data returned by tools ----------


class SizeStock(BaseModel):
    size: str
    quantity: int


class ProductSummary(BaseModel):
    """Compact product info a search tool returns to the agent."""

    product_id: str
    name: str
    garment_type: str
    colors: list[str]
    price: float
    total_stock: int
    sizes_in_stock: list[str]
    requested_size_quantity: int | None = Field(
        default=None, description="Stock in the size the shopper asked about (0 = sold out in that size)."
    )


class SearchResults(BaseModel):
    """What search_products returns: the matches shown plus how many exist in total."""

    total_matches: int = Field(description="How many catalogue items match in total (may exceed the number returned).")
    price_min: float | None = Field(description="Lowest price across ALL matches, not just the ones returned.")
    price_max: float | None = Field(description="Highest price across ALL matches, not just the ones returned.")
    products: list[ProductSummary] = Field(description="The best matches, best first.")


class ProductInfo(ProductSummary):
    """Full product record, including description and stock by size."""

    description: str
    search_tags: list[str]
    inventory: list[SizeStock]


# ---------- Lookup tool results (Problem 6) ----------
# Every lookup result carries product_id + name so the agent can cite exactly which item
# it looked up and add the id to `picks` for the page cards.

LOW_STOCK_THRESHOLD = 5


class ProductMatch(BaseModel):
    product_id: str
    name: str


class ProductNotFound(BaseModel):
    """Returned instead of guessing when a lookup doesn't match exactly one product."""

    found: Literal[False] = False
    query: str
    message: str
    suggestions: list[ProductMatch] = Field(
        default_factory=list, description="Closest catalogue matches. Retry the lookup with one of these product_ids."
    )


class ProductDescription(BaseModel):
    found: Literal[True] = True
    product_id: str
    name: str
    garment_type: str
    description: str = Field(description="Catalogue description, quote or paraphrase it; do not add details.")
    colors: list[str] = Field(description="The only colors this product comes in.")
    search_tags: list[str]


class PriceInfo(BaseModel):
    found: Literal[True] = True
    product_id: str
    name: str
    price: float = Field(description="Price in USD from the catalogue table.")
    price_display: str = Field(description='Formatted price to quote exactly, e.g. "$68.00".')
    currency: Literal["USD"] = "USD"


class SizeStatus(BaseModel):
    size: str
    quantity: int
    status: Literal["in_stock", "low_stock", "sold_out"] = Field(
        description="sold_out = 0 left; low_stock = 1-5 left; in_stock = more than 5."
    )


class StockReport(BaseModel):
    found: Literal[True] = True
    product_id: str
    name: str
    requested_size: str | None = Field(description="The size the shopper asked about (normalized), if any.")
    requested_size_status: SizeStatus | None = Field(
        description="Stock for the requested size. None if no size was asked for or the size isn't one we carry."
    )
    sizes: list[SizeStatus] = Field(description="Stock for every size, XS to XXL.")
    sizes_in_stock: list[str]
    sizes_sold_out: list[str]
    total_in_stock: int
    summary: str = Field(description="Plain-English stock statement generated from the database. Safe to repeat.")


class AlternativeItem(BaseModel):
    product_id: str
    name: str
    garment_type: str
    colors: list[str]
    price: float
    price_display: str
    quantity_in_size: int = Field(description="How many are in stock in the requested size (always > 0).")
    why_similar: list[str] = Field(description='Short reasons, e.g. ["same kind: hoodie", "shares color: navy"].')


class AlternativesResult(BaseModel):
    """Returned by find_alternatives: in-stock replacements for an item that is sold out in the shopper's size."""

    found: Literal[True] = True
    original_product_id: str
    original_name: str
    size: str
    original_quantity_in_size: int = Field(description="0 means the original is sold out in this size.")
    alternatives: list[AlternativeItem] = Field(description="Most similar first. All are in stock in `size`.")
    summary: str


# ---------- Agent dependencies & structured output ----------


class ShopperProfile(BaseModel):
    """The customer fields the agent may see. Deliberately excludes id and password_hash."""

    logged_in: bool
    first_name: str | None = None
    last_name: str | None = None
    full_name: str | None = None
    email: str | None = None
    member_since: str | None = Field(default=None, description="Date the account was created (YYYY-MM-DD).")


GUEST = ShopperProfile(logged_in=False)


class PageProduct(BaseModel):
    """A product the shopper can currently see, resolved from the database."""

    product_id: str
    name: str
    garment_type: str
    colors: list[str]
    price: float


class PageInfo(BaseModel):
    """Where the shopper is on the website, resolved server-side from the browser's PageContext."""

    path: str = "/"
    page_type: Literal["home", "products", "product_detail", "about", "account", "other"] = "other"
    listing_filter: str | None = Field(default=None, description='Products page filter, e.g. "type=hood" or "q=hockey".')
    current_product: PageProduct | None = Field(
        default=None, description='The product whose single-item page is open. "this"/"it" usually means this one.'
    )
    cards_on_screen: list[PageProduct] = Field(
        default_factory=list, description="Chat result cards currently shown on the page, in on-screen order."
    )


@dataclass
class ShopDeps:
    """Per-request context handed to the agent (PydanticAI deps). Contains no secrets or password data."""

    shopper: ShopperProfile = field(default_factory=lambda: GUEST)
    page: PageInfo = field(default_factory=PageInfo)


class CardPick(BaseModel):
    """One product the agent wants rendered as a card on the website."""

    product_id: str = Field(description="Exact product_id from a tool result in this conversation.")
    reason: str = Field(
        default="",
        max_length=90,
        description='Very short reason it matches, shown on the card, e.g. "Navy, left-chest hockey logo".',
    )


class AgentReply(BaseModel):
    """Structured output the LLM must return (the agent -> API half of the contract)."""

    reply: str = Field(description="Friendly chat answer in the Campus Customs voice.")
    results_title: str | None = Field(
        default=None,
        description='Heading for the product cards on the page, e.g. "Hoodies" or "Pierson College gear". None if no cards.',
    )
    total_matches: int | None = Field(
        default=None, description="total_matches from search_products when showing search results, else None."
    )
    picks: list[CardPick] = Field(
        default_factory=list,
        description=f"Products to render as cards on the page, best match first. Max {MAX_CARDS}.",
    )


# ---------- HTTP request / response bodies ----------


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


class PageContext(BaseModel):
    """What the browser reports about the current page. Untrusted: ids are checked against the database."""

    path: str = Field(default="/", max_length=300)
    product_id: str | None = Field(default=None, max_length=120, description="Set on /products/:productId pages.")
    listing_filter: str | None = Field(default=None, max_length=200)
    visible_product_ids: list[str] = Field(default_factory=list, max_length=24)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)
    history: list[ChatTurn] = Field(
        default_factory=list,
        max_length=40,
        description="Used for guests only; logged-in history is loaded from the database.",
    )
    page: PageContext | None = None


class ProductCard(BaseModel):
    """A product card for the website. Built from the database, never from LLM text (except `reason`)."""

    product_id: str
    name: str
    garment_type: str
    description: str
    colors: list[str]
    image_url: str
    price: float
    inventory: list[SizeStock]
    total_stock: int
    reason: str = ""


class ChatResults(BaseModel):
    """Product matches the website renders as cards (the API -> front end half of the contract)."""

    title: str
    total_matches: int
    products: list[ProductCard]


class ChatResponse(BaseModel):
    reply: str
    results: ChatResults | None = None
    status: Literal["ok", "timeout", "too_complex", "unverified"] = Field(
        default="ok",
        description="timeout / too_complex = time or step limit (Problem 9); unverified = numbers failed the check (Problem 12).",
    )
    seconds: float | None = Field(default=None, description="How long the agent took to answer.")


class SavedMessage(BaseModel):
    """One row of chat_messages, as sent to the browser when history is reloaded."""

    id: int
    role: Literal["user", "assistant"]
    content: str
    results: ChatResults | None = None
    created_at: str


class ChatHistory(BaseModel):
    logged_in: bool
    messages: list[SavedMessage] = Field(default_factory=list)
