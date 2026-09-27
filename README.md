# Campus Customs — HW 4

A customer website for **Campus Customs** ("Yale Bulldog Blue", 57 Broadway, New Haven). Shoppers can browse products, create an account, and chat with a shopping assistant that answers **honestly about price and stock from the shop's database** and puts matching items on the page as product cards.

- **Front end:** React + Vite + TypeScript (`frontend/`)
- **Back end:** FastAPI (`backend/main.py`), whose brain is a **PydanticAI agent** using OpenAI `gpt-5.6-luna` via Portkey
- **Data:** SQLite `campus_customs.db` plus product images (the local data pack, **not in this repo**)

## Repository layout

```
hw4/
├── AI_prompts.md            # prompts I typed for each problem (1–13)
├── requirements.txt         # Python dependencies for the backend
├── .env.example             # placeholder environment variables (copy to .env)
├── .gitignore               # keeps .env, the database, product images, node_modules out of git
├── README.md
├── frontend/                # Vite React TypeScript app
├── backend/
│   ├── main.py              # FastAPI app — run with: uvicorn main:app --reload --port 8000
│   ├── agent.py             # ┐
│   ├── models.py            # │ the agent: wiring, structured types,
│   ├── tools.py             # │ database tools, and system prompt
│   ├── prompts/prompt.md    # ┘
│   └── auth.py, security.py, db.py, context.py, chat_history.py, audit.py   # app support modules
└── output/
    ├── harness.md           # how the whole system works (data, tools, models, safety, specs)
    ├── design.md            # Problem 10 design changes
    ├── usability.md         # Problem 9 usability improvements
    ├── app_check.html       # Problem 11 live-site check (double-click to open)
    ├── app_check_images/    # screenshots linked from app_check.html
    └── audit_trail.json     # append-only log of agent-loop activity
```

The **agent** is the four files `backend/prompts/prompt.md`, `backend/agent.py`, `backend/tools.py`, and `backend/models.py`. The other backend modules handle login, the database connection, chat history, page context, and audit logging.

## Setup

### 1. Place the data pack (not included in git)

Put the course data pack in a `data/` folder inside `hw4/`:

```
hw4/
└── data/
    ├── campus_customs.db     # SQLite: catalogue, inventory, users, chat_messages
    └── products/             # product images; paths match catalogue.image_file_path
```

### 2. Add your API key

Copy `.env.example` to `.env` in `hw4/` and set `PORTKEY_API_KEY`. `AUTH_SECRET_KEY` and `AGENT_TIMEOUT_SECONDS` are optional. The backend also reads a `.env` in the folder above `hw4/`.

### 3. Install

Python 3.12+ and Node.js 20+ are required.

```bash
pip install -r requirements.txt
```

```bash
cd frontend
npm install
```

## Run

Use two terminals.

**Back end** (from `hw4/backend/`):

```bash
uvicorn main:app --reload --port 8000
```

**Front end** (from `hw4/frontend/`):

```bash
npm run dev
```

Open **http://localhost:5173**. Vite forwards `/api` and `/media` requests to the backend on port 8000.

**Test login:** `test@campuscustoms.yale.edu` / `password` (a seed user in the database). You can also create a new account on the Create account page.

### Things to try

- Products page: filter by category and **"In stock in my size"**, then sort by price.
- Open any product, then use **"← Back to …"** or the breadcrumbs.
- Chat (bottom-right **Ask Dan**):
  - "What hoodies do you have?" puts product cards on the page.
  - "Is the Crew Left Chest Hoodie in stock in medium?" gives an honest sold-out answer plus in-stock alternatives.
  - "Do you have this in pink?" on a product page works because the agent knows which item is open.

## API

| Endpoint | Description |
|---|---|
| `GET /api/products?q=` | All products with stock by size (optional keyword search) |
| `GET /api/products/{product_id}` | One product with stock by size |
| `GET /media/products/{file}.jpg` | Product image |
| `POST /api/auth/register` | Create account (first/last name, email, password) |
| `POST /api/auth/login` | Log in; sets an HttpOnly session cookie |
| `POST /api/auth/logout` | Log out |
| `GET /api/auth/me` | Current logged-in user (or `null`) |
| `POST /api/chat` | `{ message, history, page }` → agent `{ reply, results, status, seconds }` |
| `GET /api/chat/history` | Logged-in shopper's saved chat (last 50 messages) |

See **`output/harness.md`** for the full design: database fields, auth and password hashing, agent tools and model fields, safety rules, the audit trail, and all limits.
