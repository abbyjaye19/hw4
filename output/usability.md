# Campus Customs — Usability Improvements (Problem 9)

Four improvements, picked from a shortlist of eight (four front end, four agent/backend):

| # | Type | Improvement | Where to see it in the running app |
|---|---|---|---|
| 1 | Front end | **Easy back navigation**: "← Back to …" button, breadcrumbs, and scroll memory | Open any product from Products, Home, or the chat → top of the product page |
| 2 | Front end | **Sort + "in stock in my size" filter** | Products page, the white bar under the category pills |
| 3 | Agent / backend | **Thinking time limit**: 25 s timeout, step limit, Cancel button | Chat widget while the assistant is thinking |
| 4 | Agent / backend | **Sold-out alternatives tool** (`find_alternatives`) | Ask the chat for an item in a size that's sold out |

---

## 1. Easy back navigation (front end)

### What I added

- **"← Back to …" button** at the top of every product page. It names where the shopper came from:
  - "← Back to Hoodies", "← Back to Relatives", "← Back to Search: 'hockey'", "← Back to Home"
  - "← Back to chat results (In stock in L instead)" when the item was opened from a chat card
- **Breadcrumbs** next to it: `Home › Products › Hoodies › Yale Sports Hoodie Hockey`. Each step is a link. If the shopper opened the page directly (a shared link or a bookmark), the middle crumb is the item's category, so there's still a way to browse similar items.
- **Filters are kept.** Going back returns to the *same* list: category, search, size filter, and sort all live in the URL (e.g. `/products?type=hood&size=M&sort=price-asc`).
- **Scroll position is remembered.** `ScrollManager.tsx` saves each page's scroll position. Going back, with our button or the browser's Back button, returns to the exact spot in the grid. Any other navigation opens the new page at the top, so a product page no longer opens halfway down.

Files:
- `frontend/src/components/ScrollManager.tsx`
- `frontend/src/navigation.ts` (page labels, category crumbs)
- `frontend/src/components/ProductCard.tsx` (each card records where it was clicked from)
- `frontend/src/pages/ProductPage.tsx` (Back button and breadcrumbs)

### Why it helps

- **Shoppers:** browsing merch is "look, compare, go back, look again". Before this, the only link was "← All products", which threw away the shopper's filter and scroll position. Someone 40 cards into the hoodies had to start over after every click. Now comparing items takes one click and they never lose their place.
- **Business:** people who can compare easily look at more items and are more likely to find one they buy. Breadcrumbs also show which collection an item belongs to, which leads shoppers to similar items.

### Verified in the running app

- Products → Hoodies, size M, price low → high, scrolled to 1400 px, opened a card.
- The product page opened at the top with **"← Back to Hoodies"** and **Home › Products › Hoodies › …**.
- The Back button returned to `/products?type=hood&size=M&sort=price-asc` at **1400 px**. The browser's Back button did the same.
- From a chat card: **"← Back to chat results (In stock in L instead)"**, which returned to the page the chat was on, with the results panel still there.

---

## 2. Sort + "in stock in my size" filter (front end)

### What I added

On the Products page, a new filter bar under the category pills:

- **"In stock in my size:" chips**: Any · XS · S · M · L · XL · XXL. Picking a size hides everything that's sold out in that size, and each card shows the stock for that size ("8 left in M"; 5 or fewer is highlighted in gold).
- **Sort by**: Name (A–Z), Price low → high, Price high → low, Most in stock.
- **Result line**: "**21** items in stock in M · 6 more sold out in M". The shopper knows the filter is hiding some items, and can **Clear all filters** in one click.
- **Sold-out badge**: a red "SOLD OUT" label on any card that has no stock in any size, plus an "In stock: XS · S · M…" line on every card.
- If a size filter empties the list, the page says so and points to the chat, whose alternatives tool (improvement 4) can suggest replacements.

Backend support: `GET /api/products` now returns stock by size for every product (one extra query), so filtering and sorting happen instantly in the browser.

Files:
- `frontend/src/pages/Products.tsx`
- `frontend/src/components/ProductCard.tsx`
- `backend/main.py` (`list_products`)

### Why it helps

- **Shoppers:** before, the only way to learn a hoodie was sold out in your size was to open it. With 145 sold-out size slots across the catalogue, that was a lot of wasted clicks. Now "hoodies in stock in M, cheapest first" is two clicks. Price sorting helps budget shoppers (students) and gift buyers.
- **Business:** fewer "I clicked five things and nothing was in my size" drop-offs. "Most in stock" also lets staff or the shop push items with plenty of inventory.

### Verified in the running app

- Hoodies + M + "Price: low to high" → "**21 items in stock in M · 6 more sold out in M**".
- All 21 cards were checked against `/api/products` and are really in stock in M.
- Prices ascend from $45.00 (UA Gameday Double Knit Hood, "8 left in M") to $88.00 (Champion Full Zip Hood).

---

## 3. Thinking time limit (agent / backend)

### What I added

Three layers, so the chat can never hang or spin forever:

1. **Server timeout (25 s):** `agent.run_chat()` wraps the PydanticAI run in `asyncio.wait_for(..., timeout=25)` (configurable as `AGENT_TIMEOUT_SECONDS`). If time runs out, the shopper gets a friendly reply instead of an error: *"Sorry, that one took me too long to look up! Could you try asking in a simpler way, like 'Is the Yale Dad Hoodie in stock in M?' …"*
2. **Step limit:** `UsageLimits(request_limit=6, tool_calls_limit=10)` per message. This stops a confused agent from looping through tools. It answers: *"That question needed more lookups than I can do at once. Could you ask about one or two items at a time?"* The prompt also tells the agent to be efficient (usually 1–3 tool calls, no repeated lookups).
3. **In the browser:**
   - After 6 s the thinking dots show **"Still checking the stockroom… 7s"**.
   - A **Cancel** button stops the request right away.
   - A backup 35 s cutoff covers network trouble.
   - Time-limit replies are shown as a yellow notice bubble.

The response now includes `status` (`ok` / `timeout` / `too_complex`) and `seconds`. Timed-out attempts are **not saved** to a logged-in shopper's history and aren't sent back to the agent, so they don't clutter the conversation.

Files:
- `backend/agent.py` (`AGENT_TIMEOUT_SECONDS`, `USAGE_LIMITS`, `run_chat`)
- `backend/models.py` (`ChatResponse.status` / `seconds`)
- `backend/main.py` (skip saving non-ok replies)
- `frontend/src/components/ChatWidget.tsx`

### Why it helps

- **Shoppers:** a chat that shows dots forever feels broken, and people leave. Now there's always an answer within about 25 seconds. They can see it's working ("7s") and can stop it.
- **Business:** each model call and tool call costs money (via Portkey). The step limit caps the cost of any single message, and the timeout stops slow requests from piling up on the server.

### Verified

- **Forced timeout** (`AGENT_TIMEOUT_SECONDS=1`): returned `status: timeout` after 1.0 s with the friendly message.
- **Forced step limit** (`request_limit=1`) on a three-product comparison: returned `status: too_complex` after 2.2 s with the "one or two items at a time" message.
- **In the app:** "Still checking the stockroom… 7s" appeared during a slow answer. Clicking **Cancel** 1.5 s into "What crewnecks do you have?" showed "Okay, I stopped looking. Ask me something else anytime!" as a notice bubble.

---

## 4. Sold-out alternatives tool (agent / backend)

### What I added

A new agent tool, **`find_alternatives(product, size, limit=4)`**, in `backend/tools.py`. It returns an `AlternativesResult` (in `models.py`). Given an item and the shopper's size, it:

1. reads the original item's stock in that size (read-only database);
2. looks only at products **in stock in that size** (quantity > 0);
3. scores them by similarity:
   - **same kind of garment** (+10: hoodie, crewneck, t-shirt, quarter-zip, jacket/fleece)
   - **shared subject** (+5 each: hockey, Pierson, bulldog, dad…), from name and tag words with generic words like "drawstring" or "pocket" filtered out
   - shared layout such as a left-chest logo (+2)
   - **shared colors** (+2 each)
   - **close price** (up to +3)
4. returns the best matches, each with `price_display`, `quantity_in_size`, and plain-English `why_similar` reasons, plus a ready-to-use `summary`.

The prompt now says: when `get_stock` shows the shopper's size is sold out, say so clearly, **then call `find_alternatives`**, suggest 2–3 of them, and put them on the page as cards (title like "In stock in L instead", reasons like "In stock in L · hockey hoodie").

### Why it helps

- **Shoppers:** "sold out" used to be a dead end. Now the reply offers the closest thing they *can* buy in their size, e.g. another hockey hoodie for a hockey fan, not a random shirt.
- **Business:** it turns a lost sale into a likely sale. With 145 of 612 size slots at zero, this comes up often. Every suggestion is grounded in real stock, so the agent never recommends something that is also sold out.

### Verified

- **Tool alone:** Ice Hockey Left Chest Hoodie in L (sold out) → **Yale Sports Hoodie Hockey** first ("same kind: hoodie; similar theme: hockey"), then Squash Left Chest and Basic Hoodie Big Yale, all in stock in L.
- **Agent run:** for "I need the Ice Hockey Left Chest Hoodie in large", the agent called `search_products → get_stock → find_alternatives`.
- **In the app:** "Do you have the Ice Hockey Left Chest Hoodie in large?" → *"Sorry, the Ice Hockey Left Chest Hoodie is sold out in large. It's available in XS, S, and XXL. In large instead, the Yale Sports Hoodie Hockey, Squash Left Chest Hoodie, and Basic Hoodie Big Yale are in stock…"*. The results panel showed **"In stock in L instead"** with 4 cards, e.g. "In stock in L · hockey hoodie".

---

## Ideas considered but not built

Chat quick-reply chips · "Ask about this item" button · price-accuracy checker · response caching / cost logging.
