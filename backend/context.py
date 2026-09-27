"""Builds the agent's per-request context (ShopDeps): who is chatting and what page they are on."""

from __future__ import annotations

import json

from auth import PublicUser
from models import GUEST, PageContext, PageInfo, PageProduct, ShopDeps, ShopperProfile
from tools import read_only_db


def shopper_profile(user: PublicUser | None) -> ShopperProfile:
    """Only these customer fields reach the agent (no user id, no password hash)."""
    if user is None:
        return GUEST
    return ShopperProfile(
        logged_in=True,
        first_name=user.first_name,
        last_name=user.last_name,
        full_name=user.name,
        email=user.email,
        member_since=user.created_at[:10],
    )


def _page_type(path: str) -> str:
    if path == "/":
        return "home"
    if path == "/products":
        return "products"
    if path.startswith("/products/"):
        return "product_detail"
    if path == "/about":
        return "about"
    if path in ("/login", "/create-account"):
        return "account"
    return "other"


def _lookup(ids: list[str]) -> list[PageProduct]:
    """Resolve product ids from the browser against the catalogue; unknown ids are dropped."""
    found: dict[str, PageProduct] = {}
    unique = list(dict.fromkeys(i for i in ids if i))
    if not unique:
        return []
    with read_only_db() as conn:
        marks = ",".join("?" * len(unique))
        for row in conn.execute(f"SELECT * FROM catalogue WHERE product_id IN ({marks})", unique):
            found[row["product_id"]] = PageProduct(
                product_id=row["product_id"],
                name=row["name"],
                garment_type=row["garment_type"],
                colors=json.loads(row["colors"]),
                price=row["price"],
            )
    return [found[i] for i in unique if i in found]


def resolve_page(page: PageContext | None) -> PageInfo:
    if page is None:
        return PageInfo()
    path = page.path.split("?")[0] or "/"
    current = next(iter(_lookup([page.product_id])), None) if page.product_id else None
    return PageInfo(
        path=path,
        page_type=_page_type(path),
        listing_filter=page.listing_filter,
        current_product=current,
        cards_on_screen=_lookup(page.visible_product_ids[:24]),
    )


def build_deps(user: PublicUser | None, page: PageContext | None) -> ShopDeps:
    return ShopDeps(shopper=shopper_profile(user), page=resolve_page(page))
