# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

A user types what they're looking for in plain language — "looking for a vintage graphic tee under $30". FitFindr pulls a description, a size and a price ceiling out of that sentence, searches 40 secondhand listings for the best keyword match, picks the top result, and asks the model for one or two outfits combining it with pieces the user already owns. It finishes by writing a short caption they could post about the find. If nothing matches the search, it stops there and tells the user which of the three things they could change.

---

## Tool Inventory

### `search_listings`

- **What it does:** Searches the listings data for items matching a description. Builds a keyword set from each listing's title, description and style_tags and scores it by how many keywords overlap with the query. Optionally filters by size and by a price ceiling. Returns the highest-scoring listings first, at most `config.SEARCH_RESULT_LIMIT` (10) of them.
- **Inputs:** `description` (str, required), `size` (str or None, optional — None skips size filtering), `max_price` (float or None, optional — None skips price filtering; the ceiling is inclusive)
- **Returns:** a list of full listing dicts, best match first. Each dict has id, title, description, category, style_tags, size, condition, price, colors, brand (often None) and platform.
- **When it has nothing:** returns an empty list — not None, not an exception. The loop branches on this.
- **Size matching:** a listing's size is split on `/` and anything in parentheses is dropped, so "S/M" matches a query of "S" or "M" and "XL (oversized)" is just XL. Any size starting with "One Size" matches every query.

### `suggest_outfit`

- **What it does:** Takes a thrifted listing and the user's wardrobe and asks the model for one or two outfits combining them. The system instruction restricts it to naming only pieces from the wardrobe it was given.
- **Inputs:** `new_item` (dict — a listing dict from search_listings), `wardrobe` (dict with an `items` key holding a list of wardrobe items; items use `name`, not `title`)
- **Returns:** a non-empty string of outfit suggestions naming specific wardrobe pieces alongside the new item.
- **When it has nothing:** when `wardrobe["items"]` is empty, it states that the wardrobe is empty in the first sentence, then gives general styling advice for the item on its own. It does not raise and does not return "".

### `create_fit_card`

- **What it does:** Writes a two-to-four sentence caption about the find and the outfit, in the voice of the person who found it. The prompt asks for the item's title and price to appear in the caption and the platform to be mentioned once.
- **Inputs:** `outfit` (str — the suggestion string from suggest_outfit), `new_item` (dict — a listing dict)
- **Returns:** a caption string naming the item, its price and the platform.
- **When it has nothing:** when `outfit` is empty or whitespace-only it returns a message saying there's no outfit to caption, along with the item and price. It does not call the model and does not raise.

---

## Planning Loop

**Branch rule:** If `search_listings` returns an empty list, put a message in `session["error"]` naming what the user searched for and which of the three things they could change, and return without calling `suggest_outfit`. Otherwise take the first result, put it in `session["selected_item"]`, and continue to `suggest_outfit`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regex, in `agent.py::parse_query`. Three patterns: a price ceiling ("under $30", "max $30"), a size ("size M", or a trailing ", M"), and whatever text is left becomes the description. Sizes are matched as whole words so the "M" in "Medium Wash" isn't read as a size request. It costs nothing and returns the same answer every time, which the state criterion depends on. What it gives up is phrasing it hasn't seen — "nothing over thirty dollars" parses to no price at all, and the run then ignores the ceiling without saying so.

**What moves through the session:** `query` → `parsed` (description, size, max_price) → `search_results` (list of listing dicts) → `selected_item` (results[0]) → `outfit_suggestion` (str) → `fit_card` (str). `error` is set instead when the run stops early, and everything after that point stays None. Each tool reads its input from the session rather than from the previous call's return value, so any step's state can be printed after the fact.

---

## Sample Run

**One full query**

```
$ python agent.py

=== A query the data can match ===
[1] parse_query
      in:  looking for a vintage graphic tee under $30
      out: dict with keys: description, size, max_price
[2] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
      →    10 match(es)
[3] select_item
      out: Y2K Baby Tee — Butterfly Print ($18.0, depop)
[4] suggest_outfit
      in:  Y2K Baby Tee — Butterfly Print ($18.0, depop)
      out: Here are two outfit combinations featuring your new Y2K Baby Tee — Butterfly Print using only items from your …
      →    10 wardrobe item(s)
[5] create_fit_card
      in:  Y2K Baby Tee — Butterfly Print ($18.0, depop)
      out: Scored this Y2K Baby Tee — Butterfly Print for just $18.0 on depop, and it is honestly giving early 2000s mall…
  found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop
  outfit:   Here are two outfit combinations featuring your new Y2K Baby Tee — Butterfly Print using only items from your wardrobe:

**Outfit 1: Casual Y2K Streetwear**
* **Top:** Y2K Baby Tee — Butterfly Print
* **Bottoms:** Baggy straight-leg jeans, dark wash
* **Shoes:** Chunky white sneakers
* **Accessories:** Black crossbody bag

**Outfit 2: Edgy Contrast**
* **Top:** Y2K Baby Tee — Butterfly Print
* **Outerwear:** Black cropped zip hoodie
* **Bottoms:** Wide-leg khaki trousers
* **Shoes:** Black combat boots
* **Accessories:** Brown leather belt
  fit card: Scored this Y2K Baby Tee — Butterfly Print for just $18.0 on depop, and it is honestly giving early 2000s mall rat in the best way possible. I've been styling it with baggy dark-wash denim and chunky sneakers for daytime, but throwing on a cropped zip hoodie and combat boots gives it the exact edge I wanted. It's safe to say this little butterfly print is living in heavy rotation now.

=== A query it can't ===
[6] parse_query
      in:  designer ballgown size XXS under $5
      out: dict with keys: description, size, max_price
[7] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: [] (empty)
      →    0 match(es)
[8] branch
      →    search returned []: stopping before suggest_outfit
  stopped: Nothing in the listings matched description 'designer ballgown', size XXS, under $5.
Things to change: try broader words — 'jacket' finds more than 'cropped corduroy jacket'; drop the size, or try a neighbouring one; raise the price ceiling above $5.
  fit_card is None — it should still be None here
```

The happy path runs five steps and produces a card. The empty path stops at step 8 with `fit_card` still None — the branch rule firing.

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee'))"

[{'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.', 'category': 'tops', 'style_tags': ['y2k', 'vintage', 'graphic tee', 'cottagecore'], 'size': 'S/M', 'condition': 'excellent', 'price': 18.0, 'colors': ['white', 'pink', 'purple'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_006', 'title': 'Graphic Tee — 2003 Tour Bootleg Style', 'description': 'Vintage-style bootleg tee with faded graphic. Slightly boxy fit. 100% cotton, soft and worn-in.', 'category': 'tops', 'style_tags': ['graphic tee', 'vintage', 'grunge', 'streetwear', 'band tee'], 'size': 'L', 'condition': 'good', 'price': 24.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_017', 'title': 'Mesh Long-Sleeve Top — Black', 'description': 'Sheer black mesh long-sleeve. Great for layering under a graphic tee or over a bralette. Stretchy material, fits true to size.', 'category': 'tops', 'style_tags': ['y2k', 'grunge', 'goth', 'layering'], 'size': 'S/M', 'condition': 'excellent', 'price': 15.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_033', 'title': 'Vintage Band Tee — Faded Grey', 'description': 'Faded grey band-style tee with distressed graphic. Crew neck. Fits boxy. Well-loved but no holes or major damage.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'band tee', 'graphic tee', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 19.0, 'colors': ['grey', 'charcoal'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_011', 'title': 'Low-Rise Cargo Pants — Khaki', 'description': 'Y2K era low-rise cargo pants. Lots of pockets. Khaki color, slightly distressed at the hems. Great for layering with a long tee.', 'category': 'bottoms', 'style_tags': ['y2k', 'cargo', '2000s', 'streetwear'], 'size': 'W29', 'condition': 'fair', 'price': 27.0, 'colors': ['khaki', 'tan'], 'brand': None, 'platform': 'poshmark'}, {'id': 'lst_015', 'title': 'Vintage Graphic Hoodie — Faded Black', 'description': 'Faded black pullover hoodie with barely-visible vintage graphic on the chest. Cozy interior. Some pilling but adds to the worn-in look.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'graphic', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 26.0, 'colors': ['black', 'charcoal'], 'brand': None, 'platform': 'depop'}]
```

Six results, ranked. `lst_002` and `lst_006` lead because "graphic tee" appears in both their titles and their style_tags. `lst_017` is a mesh top that only mentions a graphic tee in passing — a known false positive of keyword overlap, kept here because it's honest about what this scoring can and can't tell apart.

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import load_listings, get_empty_wardrobe; print(suggest_outfit(load_listings()[0], get_empty_wardrobe()))"

Your wardrobe is currently empty.

However, since you're looking at these Vintage Levi's 501 Jeans, here is some great general styling advice for them on their own:

* **Keep it Casual:** Pair these classic medium-wash jeans with a simple tucked-in white t-shirt and leather belt for an effortless, timeless streetwear look.
* **Play with Proportions:** Because 501s have a classic straight leg, they look fantastic balanced with either a cropped top to accentuate the high waist or an oversized, boxy sweater for a relaxed, vintage vibe.
* **Footwear versatility:** These jeans are a blank canvas—dress them down with classic canvas sneakers, or elevate them with leather loafers or ankle boots.
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import load_listings, get_example_wardrobe; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"

Here is an outfit combining your new Vintage Levi's 501 Jeans with pieces from your wardrobe:

**Outfit:**
* White ribbed tank top
* Vintage black denim jacket
* Chunky white sneakers
* Black crossbody bag
```

All four named pieces are in the wardrobe passed in (w_003, w_006, w_007, w_010) — nothing invented.

```
$ python -c "from tools import create_fit_card, suggest_outfit; from utils.data_loader import load_listings, get_example_wardrobe; item = load_listings()[0]; print(create_fit_card(suggest_outfit(item, get_example_wardrobe()), item))"

Scored these Vintage Levi's 501 Jeans for $38 on Depop and I am officially obsessed with the medium wash. Paired them with a simple white ribbed tank, my favorite black denim jacket, and chunky sneakers for the ultimate 90s streetwear vibe. Honestly, nothing beats the fit of broken-in vintage denim.
```

The caption has the price but shortens the title to "Vintage Levi's 501 Jeans" — the full title is "Vintage Levi's 501 Jeans — Medium Wash". This is why criterion 4 targets 4 of 5 rather than 5 of 5.

---

## How I Used AI

**Moment 1**

- *What I asked for:* help writing suggest_outfit, including formatting the wardrobe items into the prompt.
- *What came back:* code that pulled `item['title']` for each wardrobe item.
- *What I changed:* wardrobe items don't have a `title` — they have `name`. Only listings have `title`. It would have crashed on every non-empty wardrobe. I checked the field names in wardrobe_schema.json and fixed it.

**Moment 2**

- *What I asked for:* a prompt for suggest_outfit that includes the item's details.
- *What came back:* `{title} ({price})` — the price as a bare number in parentheses.
- *What I changed:* the model read 38.0 as a measurement and wrote "because they are a 38-inch size," then built advice on top of that. Nothing crashed; the output was just confidently wrong. I labelled every field on its own line — Item, Category, Colors, Style tags, Price — so there's no unlabelled number to misread.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════ -->

---

## Run Log — Before

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. A matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. The selected item is the item `suggest_outfit` received | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. The fit card names the item's price and title | 4 of 5 | FAIL | PASS | FAIL | FAIL | FAIL | MISSED (1/5) |
| 5. The outfit names only items in the wardrobe | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

Run with `python run_eval.py --label before` — every scenario, five times, caching off.
Full output: `results/run_2026-10-10_1117_before.md`.

**Real output from one try**, pasted as text, naming the file and function that produced it:

**Criterion 1** — scenario `matching query completes`, query `vintage graphic tee under $30`.
Produced by `agent.py::run_agent` (the full loop), caption from `tools.py::create_fit_card`:

```
[1] parse_query → [2] search_listings (via MCP), 10 match(es) → [3] select_item
→ [4] suggest_outfit, 10 wardrobe item(s) → [5] create_fit_card
```

```
scored this Y2K Baby Tee — Butterfly Print for $18.0 on depop and I'm obsessed with the pink and purple graphic. I threw it on with some baggy dark wash jeans and chunky sneakers for an easy streetwear vibe, but I love how it looks layered under my black zip hoodie with combat boots too. honestly one of my best vintage scores yet.
```

**Criterion 2** — scenario `impossible query stops early`, query `designer ballgown size XXS under $5`.
Produced by `agent.py::_nothing_found_message`, called from `agent.py::run_agent`:

```
Nothing in the listings matched description 'designer ballgown', size XXS, under $5.
Things to change: try broader words — 'jacket' finds more than 'cropped corduroy jacket'; drop the size, or try a neighbouring one; raise the price ceiling above $5.
```

**Criterion 3** — scenario `state carries the selected item forward`, try 1.
Produced by `agent.py::run_agent`, printed via `trace.py::step`:

```
[3] select_item
      out: Y2K Baby Tee — Butterfly Print ($18.0, depop)
[4] suggest_outfit
      in:  Y2K Baby Tee — Butterfly Print ($18.0, depop)
```

**Criterion 4** — scenario `fit card names price and title`, item `Suede Chelsea Boots — Tan` ($44.0).
Produced by `tools.py::create_fit_card`:

```
Try 1 (FAIL — price present, full title not):
Found these vintage Suede Chelsea Boots on Poshmark for just $44 and I am officially obsessed. They look so good dressed down with a white tank and baggy dark wash jeans, but I'm also really leaning into that cozy earth-tone vibe with oversized grey sweats and khaki trousers. Absolute fall shoe goals.

Try 2 (PASS — both present):
Scored these Suede Chelsea Boots — Tan for just $44 on Poshmark and I'm obsessed. They add the absolute best vintage Western touch whether I'm throwing them on with baggy dark-wash denim or keeping it cozy in wide-leg khakis. Such a good earth-toned staple for fall.
```

**Criterion 5** — scenario `outfit grounded in wardrobe`, try 1.
Produced by `tools.py::suggest_outfit`:

```
Here are two outfit combinations using your new light wash cropped denim jacket and pieces from your wardrobe:

**Outfit 1: Casual Streetwear**
*   White ribbed tank top
*   Baggy straight-leg jeans, dark wash
*   Chunky white sneakers
*   Black crossbody bag

**Outfit 2: Contrast Denim Look**
*   Black cropped zip hoodie
*   Wide-leg khaki trousers
*   Chunky white sneakers
*   Brown leather belt
```

All eight named pieces are in the example wardrobe — nothing invented.

**On the three failure modes:** all three were triggered deliberately and all three
already return a user-readable message rather than a crash or silence — an empty
search stops at the branch and names what to change, an empty wardrobe returns
general styling advice, and an unreachable model returns a sentence pointing at
`GEMINI_API_KEY` while keeping the search results. No new handler was needed.

---

## Verdicts and Diagnoses

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 | A matching query completes all three tools | 4 of 5 | MET (5/5) | All five tries ran steps [1]–[5] and returned a fit card. |
| 2 | An impossible query stops before the second tool | 5 of 5 | MET (5/5) | All five stopped at `[3] branch` with the "nothing matched" message and `fit_card` still None. |
| 3 | The selected item is the item `suggest_outfit` received | 5 of 5 | MET (5/5) | In all five tries the item at `[3] select_item` is the item at `[4] suggest_outfit in:`. |
| 4 | The fit card names the item's price and title | 4 of 5 | MISSED (1/5) | The price appeared in all five cards; the full title `Suede Chelsea Boots — Tan` appeared in only one. Read plainly, that's 1 of 5 against a target of 4 of 5. |
| 5 | The outfit names only items in the wardrobe | 5 of 5 | MET (5/5) | Every garment named across all five outfits is in the example wardrobe. Nothing invented. |

**Diagnoses**

**Criterion 4 — MISSED (1/5). Where it failed: the model's output, in `tools.py::create_fit_card`.**

The tool itself worked — it returned a caption of the right length, with the price and the platform, on all five tries. The failure is in what the model wrote. The item's title is `Suede Chelsea Boots — Tan`, and four of five cards rendered it as "Suede Chelsea Boots" or "vintage Suede Chelsea Boots", dropping the `— Tan` colour suffix.

The mechanism: my prompt asks for "the item's title and price to appear in the caption", but it never tells the model to reproduce the title *verbatim*, and the caption is explicitly asked for in a casual, first-person voice. Given a title with an em-dash descriptor, the model treats the part after the dash as optional descriptive detail and rewrites the whole thing into natural prose — exactly what a caption-writing instruction invites. The price survived because `$44` is a single token with nothing to paraphrase; the title didn't because it's a phrase the model feels free to reword.

**The pattern: this is one problem, not two.**

The same paraphrasing shows up in a different tool. In the `outfit grounded in wardrobe` scenario, all five outfits from `tools.py::suggest_outfit` refer to the item as "your new light wash cropped denim jacket" — never the actual title, `Denim Jacket — Light Wash, Cropped`. Two tools, two prompts, one mechanism: neither prompt requires the exact title string, so the model rewrites titles into prose in both places. That means one fix should move both, which is what Milestone 5 tests.

**A second failure found while testing, outside the five criteria.**

On the empty-wardrobe path, try 1 of the `empty wardrobe` scenario produced this caption from `tools.py::create_fit_card`:

> "...hits right at the waist, so I threw it over **my empty wardrobe** for an effortlessly cool, balanced look."

Where it failed: the model's output again, but the cause is upstream. `create_fit_card` takes the outfit string as its input, and on the empty-wardrobe path that string opens with "Your wardrobe is currently empty." The model read that sentence as outfit content and folded "empty wardrobe" into the caption as though it were a garment. The tool worked and nothing raised; the prompt assumed the outfit string always describes wearable items, which isn't true on this path. It only appears when the wardrobe is empty, which is why none of the five criteria caught it.

**Nothing was revised.** Criterion 4 was measurable as written and I missed it, so the target stays at 4 of 5 and gets a fix attempted instead. One measurement note on criterion 3: my criterion names the item's `id`, but `trace.py::_short` renders item dicts as title/price/platform, so what I actually compared was title + price + platform across `[3] select_item` and `[4] suggest_outfit`. Same item, five of five — but worth stating that the id itself isn't what's printed.

---

## Loop Trace

**Happy path**

```
[1] parse_query
      in:  cernucci jacket XXL
      out: dict with keys: description, size, max_price
[2] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: 4 items: 90s Track Jacket — Navy/White Stripe, Denim Jacket — Light Wash, Cropped … +1 more
      →    4 match(es)
[3] select_item
      out: 90s Track Jacket — Navy/White Stripe ($45.0, poshmark)
[4] suggest_outfit
      in:  90s Track Jacket — Navy/White Stripe ($45.0, poshmark)
      out: Here are two outfit combinations using your new 90s Track Jacket…
      →    10 wardrobe item(s)
[5] create_fit_card
      in:  90s Track Jacket — Navy/White Stripe ($45.0, poshmark)
      out: Scored this 90s Track Jacket — Navy/White Stripe for $45.0 on Poshmark…
```

**Empty search**

```
[1] parse_query
      in:  cernucci winter jackets
      out: dict with keys: description, size, max_price
[2] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: [] (empty)
      →    0 match(es)
[3] branch
      →    search returned []: stopping before suggest_outfit
```

The empty path is two steps shorter and never reaches `suggest_outfit` — the branch rule firing.

**On the MCP move:**

I registered `search_listings` as a tool on the MCP server (`mcp_server.py`, `@mcp.tool()` with a typed signature and a written description). In `run_agent()` the direct `search_listings(...)` call now goes through `_search()`, which calls `call_tool("search_listings", {...})` over MCP, with a fallback to the direct call if the server is unavailable. The return shape — a list of listing dicts — was unchanged, so every step after search (branch, select_item, suggest_outfit, create_fit_card) behaved identically.

One thing worth noting: the trace label `search_listings (via MCP)` is a hardcoded string, so it prints whether the MCP call or the fallback ran — it is not by itself proof that MCP was used. I verified the real path by temporarily printing inside both branches of `_search`, and confirmed the MCP branch executed (`>>> used MCP`), not the fallback.

---

## The Improvement

**What I changed:**

One change, to the prompt in `tools.py::create_fit_card`. The instruction used to read:

> "Include the item's title and its price in the caption, and mention the platform once."

It now reads:

> "The caption must contain the item's title EXACTLY as written below — word for word, including everything after any dash. Do not shorten it, reword it, or drop the colour. Include its price too, and mention the platform once."

Nothing else was touched — not the system prompt, not the field lines, not the empty-outfit guard, and not `suggest_outfit`. One change so the result is attributable.

**Which failure it was meant to fix:**

Criterion 4, which came in at 1 of 5 against a target of 4 of 5. The diagnosis said the tool worked and the prompt was at fault: it asked for "the title" without asking for it verbatim, while the system prompt simultaneously told the model to write like a person and not a product listing. Faced with `Suede Chelsea Boots — Tan`, the model resolved that tension by treating the colour suffix as droppable prose. The fix removes the ambiguity rather than papering over it in code — a string check with a retry would have raised the score without addressing why the model was dropping it.

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. A matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. The selected item is the item `suggest_outfit` received | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. The fit card names the item's price and title | 4 of 5 | PASS | PASS | PASS | PASS | PASS | **MET (5/5)** — was 1/5 |
| 5. The outfit names only items in the wardrobe | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

Run with `python run_eval.py --label after` — same scenarios, same five tries, caching off.
Full output: `results/run_2026-10-10_1152_after.md`.

**Did it help, and how do I know:**

Yes. Criterion 4 went from **1 of 5 to 5 of 5**, which is the only row that moved, and it moved from MISSED to MET. All five captions now carry the title in full, where before only one did:

```
Try 1: Scored these Suede Chelsea Boots — Tan for $44.0 on poshmark and I'm obsessed...
Try 2: Scored these Suede Chelsea Boots — Tan for just $44.0 on poshmark, and they completely tie my earth-toned look...
Try 3: Scored these gorgeous Suede Chelsea Boots — Tan for just $44.0 on poshmark and I'm obsessed...
Try 4: Scored these Suede Chelsea Boots — Tan for just $44.0 on poshmark and I'm obsessed...
Try 5: Found these Suede Chelsea Boots — Tan on poshmark for just $44.0 and I am obsessed...
```

Two things make me confident this is the change and not noise. First, the effect generalised to items the fix was never tested against: the denim-jacket captions in the other scenarios now read "Denim Jacket — Light Wash, Cropped" verbatim, where in the before run every one of them said "vintage light wash cropped denim jacket". Second, nothing else moved — criteria 1, 2, 3 and 5 are unchanged, which is what should happen when only one model-calling prompt is edited.

The caption voice did not suffer. The cards still read like posts rather than product listings; the model just anchors on the real title now instead of rewriting it.

---

## What's Still Broken

**1. `suggest_outfit` still paraphrases item titles.** My diagnosis claimed one mechanism showing up in two tools, and I only fixed one of them. In the after run, every outfit from `tools.py::suggest_outfit` still opens "your new light wash cropped denim jacket" rather than `Denim Jacket — Light Wash, Cropped`. This is the expected result of changing one prompt and not the other — it confirms the mechanism rather than undermining it — but half the pattern is still live. The fix is the same verbatim-title instruction added to `suggest_outfit`'s prompt. I left it because Milestone 5 asks for one change measured properly, and fixing both would have made the result unattributable.

**2. The empty-wardrobe caption bug is unresolved, not fixed.** The "I threw it over my empty wardrobe" nonsense did not recur in any of the five empty-wardrobe cards in the after run. I am not calling it fixed: it only appeared in 1 of 5 tries in the before run, so it was intermittent to begin with and five clean tries is weak evidence. The real fix is to stop passing the "Your wardrobe is currently empty" sentence into `create_fit_card` as though it were outfit content — either by having `suggest_outfit` return the empty-wardrobe advice under a separate key, or by having `create_fit_card` detect that path and caption the item alone. I did not attempt it because it is a second change and would have contaminated the measurement of the first.

**3. Criterion 3 is measured by proxy.** My criterion names the item's `id`, but the trace renders item dicts as title/price/platform, so what I actually compared was title + price + platform. It is met five of five on that basis and I believe it, but a stricter check would compare `session["selected_item"]["id"]` against the id of the dict `suggest_outfit` received. I would add that assertion before relying on this criterion in a future unit.

**4. The search is still a plain keyword overlap.** Outside the five criteria, but worth naming: `search_listings` returns a mesh top for "graphic tee" because the phrase appears in the description, and "nothing over thirty dollars" parses to no price ceiling at all. Both are known and documented above rather than fixed, because neither was what this unit's test pointed at.

<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [x] criteria.md has five numbered criteria, each with a target
       [x] Each criterion has a reason underneath it
       [x] All five unit 3 sections above have real content
       [x] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [x] Planning Loop names the branch rule and agent.py::run_agent
       [x] Sample Run: one full query plus the three per-tool tests, as text
       [x] At least four new commits
       [x] Repository URL submitted

     SUBMISSION CHECKLIST — unit 4

       [x] mcp_server.py exists with one tool registered
       [x] Run Log — Before, five criteria, five tries each
       [x] Real output pasted underneath, naming file and function
       [x] A verdict on every criterion
       [x] A diagnosis for every miss, naming a place AND a mechanism
       [x] Loop Trace, with the MCP call visible in it
       [x] All three failure modes triggered and handled
       [x] One improvement, with Run Log — After in the same format
       [x] What's Still Broken
       [x] At least four new commits
       [x] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**