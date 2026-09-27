# AI Prompts Log — HW 4: Campus Customs

A log of the prompts I typed into my vibe coder (Claude Code) for each problem.

---

## Project Setup (before Problem 1)

**Prompt 1:**

> I am working in HW 4 - please unzip the data pack that is in there. For this HW - a company "campus customs" needs a customer website with a chatbox - I will build a react + vite script front end and a python fastAPI backend whose brain is a pydanticAI agent. Shoppers should be able to browse products, create an account, chat about merch, see matching items appear on the page, and get honest answers about price and stock from local database.
>
> I have campus_customs.db with tables for the product catalogue, inventory by size, and users (with hashed passwords). Product image file paths are in the catalogue table. Research yalebulldogblue.com to learn the style of Campus Customs page and information.
>
> Please use the PORTKEY_API_KEY. I will now work on various HW problems for HW 4. In the end I will push the project to a public GitHub repo and submit the repo URL - do not commit the database or product images
>
> Data overview:
> - Data/campus_customs.db - SQLite database with tables catalogue, inventory and users (one test user is already there)
> - Data/products/ - product images; paths match the catalogue table

**Follow-up prompt:** None needed yet.

---

## Problem 1: AI Prompts Log

**Prompt 1:**

> Now I am on problem 1: Please create AI_prompts.md and keep it updated as I work - this file is the log of what I typed into my vibe coder. Please put one section for each problem - each section must include:
> - The problem number and title
> - At least one prompt I typed
> - A follow up prompt if needed (and one sentence on what was lacking after the first)
>
> The running site, database writes and the screenshots are the evidence - I do not need an extra proof essay beyond these prompts

**Follow-up prompt:** None needed yet.

---

## Problem 2: Understand the Database / Start the Harness

**Prompt 1:**

> Now I am on problem 2: Look at the database data/campus_customs.db and understand the fields of each table. At a minimum you should understand catalogue, inventory and users. Please start the file output/harness.md. Write down each table and its fields and one short line on why each field matters for the shop or the chatbot. I will keep growing this harness file in later problems (models, tools, safety, specs).

**Follow-up prompt:** None needed yet.

---

## Problem 3: Scaffold the React + Vite Front End

**Prompt 1:**

> Now I am on problem 3: Scaffold a React + Vite + TypeScript front end for Campus Customs. Please put a nav bar at the top that links to the main pages:
> - Home
> - Products
> - About us
> - Login
> - Create account
>
> Pull Campus Customs-style wording from yalebulldogblue.com for Home and About us, but write these pages in my own voice (I will provide this next)
>
> On the Products page, show product images from the catalogue (use the image paths in the database) with basic product info (name, price, short description)
>
> Please make each product open a single-item page (large image on one side, full product text on the other - description, price, sizes/stock when you have them). Clicking a card on Products should take the shopper there. Please also add a chat interface in the bottom right of the site (floating chat panel). It does not need to talk to an agent yet - a stub that will call your backend later is enough for this problem.
>
> A small API will be needed soon to read the database - it is fine to start a simple FastAPI app in backend/main.py just to serve products and images, then grow it into the agent backend in Problem 5.

**Follow-up prompt:**

> Follow-up: Do copy the site text for the Home and About us pages. For the Home page, please have it be a clean, easy to navigate page because many people will be clicking on this. Have a short line with Yale's slogan of "Boola Boola" on it or Go Bulldogs or something about Handsome Dan. Say it is Handsome Dan's favorite clothing store. For the About us page, explain what Campus Customs is, make it fun and say something showing it is a Yale clothing/accessories store with a creative twist

*What was lacking after the first prompt:* The Home and About us pages only had placeholder wording lifted from yalebulldogblue.com, not my own voice, and the Home page needed to be simpler and more personal (Boola Boola / Handsome Dan).

---

## Problem 4: Create Account / Login Flow

**Prompt 1:**

> I am now on problem 4: build a normal create-account/login flow.
> - Create account: first name, last name, email, password (confirm password is a nice touch to add too)
> - Log in: email and password
>
> New accounts go into the users table. Make sure to store passwords securely so hackers (both human and AI) cannot access them.
>
> The seed database already has a test user you can use while building.
> - Email: test@campuscustoms.yale.edu
> - Password: password
>
> Please confirm I can log in as that user, and that a brand-new account I create also works. Please update output/harness.md with how auth works (what you store for a user and how passwords are protected)

**Follow-up prompt:** None needed yet.

---

## Problem 5: PydanticAI Chat Agent Behind FastAPI

**Prompt 1:**

> I am now on problem 5: Please build the shop chatbox as a PydanticAI agent behind FastAPI, plugged into the front-end chat widget. Please put the API app in backend/main.py - which is the file you run with Uvicorn. Please keep the agent as these four files next to it (same ideas as HW3):
> - Backend/prompts/prompt.md - system prompt (grow this same file later)
> - Backend/agent.py - agent entry/wiring
> - Backend/tools.py - tools the agent can call
> - Backend/models.py - Pydantic/PydanticAI structured types
>
> In main.py, expose a chat route so a message from the website returns a reply from the agent (and whatever else you need for products/auth). You will need your AI model API key for the agent.
>
> Please put Campus Customs voice and safety basics into prompts/prompt.md (you will expand tools and safety later). Start or update types in models.py for chat replies/product cards as needed. In output/harness.md, please note how the front end talks to FastAPI and how the agent is loaded (prompt file + model). Make sure the backend runs from the backend/ folder like this: uvicorn main:app --reload --port 8000

**Follow-up prompt:** None needed yet.

---

## Problem 6: Database Lookup Tools (Description, Price, Stock)

**Prompt 1:**

> I am now on problem 6: please give the agent tools that look up real information from campus_customs.db:
> - Product description
> - Price
> - How many are in stock (by size when the customer asks)
>
> The agent must use the database - it should not invent prices or quantities. If a size is out of stock, say so clearly please.
>
> Please expand prompts/prompt.md so the agent knows to call these tools for price and stock questions. Please add or update return types in models.py. In output/harness.md, list each tool and explain which model fields you chose for lookup results and why.

**Follow-up prompt:** None needed yet.

---

## Problem 7: Dynamic Product Cards from Chat Search

**Prompt 1:**

> I am on problem 7 now. I want to add a neat feature to the site. When a customer asks about a type of item (for example "what hoodies do you have?") the agent should search the catalogue and the website should dynamically show those matching items as product cards (images, name, price, short info.). This is an API contract: the agent returns structured product matches and then the front end renders them on the website. After the dynamic product cards are loaded by this new feature, make sure the same single-item page behavior that was built in Problem 3 still works: each product card - including the ones that the chat just put on the page - should still open that detail view (large image + full info) when clicked. Update prompts/prompt.md and output/harness.md so it is very clear how search results reach the page.

**Follow-up prompt:** None needed yet.

---

## Problem 8: Saved Chat History, Shopper Identity, and Page Context

**Prompt 1:**

> I am now on problem 8. When a shopper is logged in, please save their chat history in the database in an appropriate table and reload it when they return to the page. The agent should know who is chatting (name, email) - put that in agent deps (or an equivalent clear pattern) and/or tools the agent can call. Also pass enough page context that if someone is on a product page and asks "do you have this in pink?" the agent knows which items they mean (Hint: you can put code into the agent context).
>
> Guests can still chat, but history only needs to persist for logged-in users. Document in output/harness.md: how user chat history is stored, what customer fields the agent sees and how the page context is passed

**Follow-up prompt:** None needed yet.

---

## Problem 9: Usability Improvements (2 Front-End + 2 Agent/Backend)

**Prompt 1:**

> I am now on problem 9: Now that the core shops works, I want to improve it. Choose and implement:
> - 2 front-end usability improvements
>   - Please provide me some ideas I can choose from and do not implement until I choose but one I thought of is the ability to click back to the previous tab easily so shoppers can use the site easier
> - 2 agent/backend usability improvements
>   - Please provide me some ideas I can choose from and do not implement until I choose, but one I thought of is if someone asks something to the chat box and the chat does not know the answer, have a time limit for thinking so it does not get stuck forever
>
> Front-end improvements are things that make the site look better and make it easier to use. Agent/backend improvements are things that make the agent output better, more accurate, or safer. These could be new agent tools or things that make the agent run faster or cheaper.
>
> Please write output/usability.md before or as you build. For each of the improvements, say:
> - What you added
> - Why it helps a Campus Customs shopper or the business
>
> Then make sure all improvements actually show up in the running app. Graders will read the write-up and look for the features.

**Follow-up prompt** (my picks from the idea list the vibe coder gave me):

> Front end: Easy back navigation (my idea), Sort + in-stock filters. Agent/backend: Thinking time limit (my idea), Sold-out alternatives tool.

*What was lacking after the first prompt:* The first prompt asked for ideas rather than a final list, so nothing could be built until I chose two front-end and two agent/backend improvements from the options.

---

## Problem 10: Creative Design Refresh

**Prompt 1:**

> I am now on problem 10: I am looking to add creative designs:
> - Have it be all navy, white, and light blue, maybe add some silver or gold metallic in there too (I am a huge fan of mixing silver and gold personally so maybe some silver/gold accents). Make sure handsome dan is on there (or just a cartoon bulldog). Have the chat still feel sophisticated, I do not want customers thinking it is an unserious website. Please make the font professional but still fun - maybe have some odes to New Haven/CT/New England in there such as cartoon pizza slices, maybe slight coastal or fall vibes, etc. Have the chatbox blend in with the theme so it is not taking attention away from the products, but still easy to find and use. Make sure the different pages/headers are easy to see and navigate.
>
> Please write output/design.md: what I changed and why it should help customers stick around and buy. Keep this concrete and short.
>
> Please open the website in my browser after making these updates so I can check.

**Follow-up prompt:** None needed yet.

---

## Problem 11: Live App Check (output/app_check.html)

**Prompt 1:**

> I am now on Problem 11: Please test of the live site and document it in output/app_check.html (a page you can double-click open). Please include clear screenshots and short captions for:
> 1. Chat checking the inventory level of an item (honest stock/price from the DB)
> 2. The dynamic search-result cards appearing after a category question (ex: hoodies)
> 3. One of the usability features that was added in Problem 9
>
> Please make the HTML easy to grade: heading for each check, screenshot, one or two sentences on what the screenshot proves. Put the screenshot image files in output/app_check_images/ and link them from app_check.html with relative paths (ex: app_check_images/inventory.png)

**Follow-up prompt:** None needed yet.

---

## Problem 12: Audit Trail, Safety Rules, and Final Harness

**Prompt 1:**

> I am now on problem 12: Please Keep an append-only output/audit_trail.json of agent-loop activity (time, tool name, short args/result, stop reason). Do not wipe it between runs. Also please think of some safety rules to give the agent and put them in prompts/prompt.md:
> - Please provide me some safety rules as ideas, some I have are not to use random internet data, do not make up numbers, do not have the chatbox thinking indefinitely etc. Please do not implement until I choose which ones to add
>
> Once I choose these, please finish output/harness.md so it is clear how the system works
> - Model fields in models.py and why I chose them
> - Tools and abilities
> - Safety rules
> - Specs (loop limits, result caps, models, how to run front + back)

**Follow-up prompt 1** (my picks from the safety-rule ideas the vibe coder gave me):

> Honesty: Shop data only (my idea), Never invent numbers (my idea), No endless thinking (my idea), No promises it can't keep. Privacy: Protect personal data, Abuse & cost limits.

*What was lacking after the first prompt:* The first prompt asked for safety-rule ideas rather than a final list, so the rules could not be written into prompt.md until I chose them.

**Follow-up prompt 2:**

> please check every question is correct and answered. Is there anything not answered or running incorrectly? double check this all please quickly before I get to the last question

*What was lacking:* I wanted a final end-to-end check that every problem's deliverable exists and the app still runs correctly after all the changes.

---

## Problem 13: Push to a Public GitHub Repository

**Prompt 1:**

> Now I am on problem 13 (the last one): please put the code in a folder named hw4 and push it to a public GitHub repository. I need the repo URL to submit with hw assignment (not a zip) - make sure the grader can open this link and clone
>
> Please do not put the real .env, campus_customs.db, or product images in the GitHub repo. Use .gitignore. Include .env.example with placeholders only. This is the expected file layout, does it match mine? *(expected layout: hw4/ with AI_prompts.md, requirements.txt, .env.example, .gitignore, README.md, frontend/, backend/ (main.py, agent.py, models.py, tools.py, prompts/prompt.md), output/ (harness.md, design.md, usability.md, app_check.html, app_check_images/, audit_trail.json); data/ stays local-only)*
>
> Also, the agent itself is four files under backend/: prompts/prompt.md, agent.py, tools.py, and models.py. README.md should explain how to run the front end and back end after placing the data pack.

**Follow-up prompt:** None needed yet.

---
