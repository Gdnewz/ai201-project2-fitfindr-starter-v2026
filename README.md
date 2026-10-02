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

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- Three or four sentences: what a user asks for, and what they get back. -->
A user types what they're looking for in plain language — "looking for a vintage graphic tee under $30". FitFindr pulls a description, a size and a price ceiling out of that sentence, searches 40 secondhand listings for the best keyword match, picks the top result, and asks the model for one or two outfits combining it with pieces the user already owns. It finishes by writing a short caption they could post about the find. If nothing matches the search, it stops there and tells the user which of the three things they could change.


---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Searches the listings data for items matching a description. Builds a keyword set from each listing's title, description and style_tags and scores it by how many keywords overlap with the query. Optionally filters by size and by a price ceiling. Returns the highest-scoring listings first, at most `config.SEARCH_RESULT_LIMIT` (10) of them.
- **Inputs:** `description` (str, required), `size` (str or None, optional — None skips size filtering), `max_price` (float or None, optional — None skips price filtering; the ceiling is inclusive)
- **Returns:** a list of full listing dicts, best match first. Each dict has id, title, description, category, style_tags, size, condition, price, colors, brand (often None) and platform.
- **When it has nothing:** returns an empty list — not None, not an exception.The loop branches on this.
- **Size matching:** a listing's size is split on `/` and anything in parentheses is dropped, so "S/M" matches a query of "S" or "M" and "XL (oversized)" is just XL. Any size starting with "One Size" matches every query.

### `suggest_outfit`

- **What it does:** Takes a thrifted listing and the user's wardrobe and asks the model for one or two outfits combining them. The system instruction restricts it to naming only pieces from the wardrobe it was given.
- **Inputs:** `new_item` (dict — a listing dict from search_listings),`wardrobe` (dict with an `items` key holding a list of wardrobe items; items use `name`, not `title`)
- **Returns:** a non-empty string of outfit suggestions naming specific wardrobe pieces alongside the new item.
- **When it has nothing:** when `wardrobe["items"]` is empty, it states that the wardrobe is empty in the first sentence, then gives general styling advice for the item on its own. It does not raise and does not return "".

### `create_fit_card`

- **What it does:** Writes a two-to-four sentence caption about the find and the outfit, in the voice of the person who found it. The prompt asks for the item's title and price to appear in the caption and the platform to be mentioned once.
- **Inputs:** `outfit` (str — the suggestion string from suggest_outfit), `new_item` (dict — a listing dict)
- **Returns:** a caption string naming the item, its price and the platform.
- **When it has nothing:** when `outfit` is empty or whitespace-only it returns a message saying there's no outfit to caption, along with the item and price. It does not call the model and does not raise.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If `search_listings` returns an empty list, put a message in `session["error"]` naming what the user searched for and which of the three things they could change, and return without calling `suggest_outfit`. Otherwise
take the first result, put it in `session["selected_item"]`, and continue to `suggest_outfit`.
**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** <!-- regex, string splitting, or asking the model — say which --> Regex, in `agent.py::parse_query`. Three patterns: a price ceiling ("under $30", "max $30"), a size ("size M", or a trailing ", M"), and whatever text is left becomes the description. Sizes are matched as whole words so the "M" in "Medium Wash" isn't read as a size request. It costs nothing and returns the same answer every time, which the state criterion depends on. What it gives up is phrasing it hasn't seen — "nothing over thirty dollars" parses to no price at all, and the run then ignores the ceiling without saying so.

**What moves through the session:** <!-- which fields, in what order -->`query` → `parsed` (description, size, max_price) → `search_results` (list of listing dicts) → `selected_item` (results[0]) → `outfit_suggestion` (str) →
`fit_card` (str). `error` is set instead when the run stops early, and everything after that point stays None. Each tool reads its input from the session rather than from the previous call's return value, so any step's state can be printed
after the fact.

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

Six results, ranked. `lst_002` and `lst_006` lead because "graphic tee" appears in
both their titles and their style_tags. `lst_017` is a mesh top that only mentions
a graphic tee in passing — a known false positive of keyword overlap, kept here
because it's honest about what this scoring can and can't tell apart.

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

All four named pieces are in the wardrobe passed in (w_003, w_006, w_007, w_010) —
nothing invented.

```
$ python -c "from tools import create_fit_card, suggest_outfit; from utils.data_loader import load_listings, get_example_wardrobe; item = load_listings()[0]; print(create_fit_card(suggest_outfit(item, get_example_wardrobe()), item))"

Scored these Vintage Levi's 501 Jeans for $38 on Depop and I am officially obsessed with the medium wash. Paired them with a simple white ribbed tank, my favorite black denim jacket, and chunky sneakers for the ultimate 90s streetwear vibe. Honestly, nothing beats the fit of broken-in vintage denim.
```

The caption has the price but shortens the title to "Vintage Levi's 501 Jeans" —
the full title is "Vintage Levi's 501 Jeans — Medium Wash". This is why criterion 4
targets 4 of 5 rather than 5 of 5.



## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:* help writing suggest_outfit, including formatting the
  wardrobe items into the prompt.
- *What came back:* code that pulled `item['title']` for each wardrobe item.
- *What I changed:* wardrobe items don't have a `title` — they have `name`. Only
  listings have `title`. It would have crashed on every non-empty wardrobe. I
  checked the field names in wardrobe_schema.json and fixed it.

**Moment 2**

- *What I asked for:* a prompt for suggest_outfit that includes the item's details.
- *What came back:* `{title} ({price})` — the price as a bare number in parentheses.
- *What I changed:* the model read 38.0 as a measurement and wrote "because they
  are a 38-inch size," then built advice on top of that. Nothing crashed; the output
  was just confidently wrong. I labelled every field on its own line — Item,
  Category, Colors, Style tags, Price — so there's no unlabelled number to misread.
<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [\] criteria.md has five numbered criteria, each with a target
       [\] Each criterion has a reason underneath it
       [\] All five unit 3 sections above have real content
       [\] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [\] Planning Loop names the branch rule and agent.py::run_agent
       [\] Sample Run: one full query plus the three per-tool tests, as text
       [\] At least four new commits
       [\] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
