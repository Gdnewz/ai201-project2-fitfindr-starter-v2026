FitFindr — my notes
How I got to my criteria (Milestone 3)

The rule I used: a criterion has to be checkable by looking at the output, not by judging whether it reads well. “The outfit suggestion is good” can’t be scored. “The names it mentions appear in the wardrobe I passed in” can.

Then the target depends on how much room the model has to be right in different words:

5 of 5 for things that are either right or wrong. The returned id either matches the item the loop forwarded or it doesn’t — there’s no phrasing involved, so anything under 5 of 5 is a real defect, not variance. Same for wardrobe items: either the name is in the wardrobe or the model made it up.
4 of 5 where the model can legitimately phrase it differently. The fit card has to contain the price and the title, but titles are long and a caption that drops a word or two from one is still doing its job. Price and title aren’t equally fragile, so demanding 5 of 5 would fail runs that are actually fine.

The reason behind each one is the same question: what goes wrong for the user if this fails? A wrong id means the agent recommended an outfit for an item the user never asked about, and nothing in the output would reveal it. Naming a wardrobe item the user doesn’t own is a false claim about their own data. Those are worth a strict target. A caption that’s slightly loose with wording isn’t.

Unit 3, Milestone 4 notes — building the tools
The tools were stubs

All three functions in tools.py had return [] as their whole body. Every empty result I got was correct behavior for a function that does nothing. When a function returns nothing for every input, read the body before testing more inputs.

Bugs already in the starter
import re was missing — _keywords would crash the moment it ran.
_size_tokens had p.strip().upper with no parentheses, so the set filled with method objects instead of strings. The error surfaced three functions away. Same mistake as return bool instead of return True in the linter.
Python things I got wrong
and evaluates left to right, so the None guard has to go on the left or the comparison crashes before the guard is reached.
Every continue has to come before the append, or it can’t prevent anything.
Never remove from a list you’re looping over — removing shifts everything left while the loop moves right, so it silently skips items.
To sort by score, append (score, listing) pairs so the score survives the loop, sort with key=lambda x: x[0], reverse=True, then strip the scores off and slice to config.SEARCH_RESULT_LIMIT (10).
What this means for my criteria

Criterion 1 — the returned id must be the right item.
Keyword overlap can’t tell what an item IS from what it MENTIONS. Searching “graphic tee” returns lst_017, a black mesh top, because its description says “great for layering under a graphic tee.” Matching on description alone it scored 2 — tied with lst_002, the real baby tee. A tie means the wrong item could come out first, and the loop hands the first result to suggest_outfit.

I widened the match to title + description + style_tags. Now lst_002 ranks first and lst_017 third. The false positive is still in the results, it just no longer wins — scoring across more fields rewards items that ARE the thing over items that mention it.

Still a risk: nothing stops a future query from tying again. Criterion 1 is testing exactly this, so if it misses, the diagnosis is the scoring, not the loop.

Criterion 5 — empty wardrobe must say so rather than invent items.
get_empty_wardrobe() in utils/data_loader.py returns the empty case already built, so I can trigger it on purpose instead of constructing one by hand.

suggest_outfit — what the model does with a sloppy prompt

My first prompt put the price in bare parentheses: {title} ({price}). The model read 38.0 as a measurement and wrote “because they are a 38-inch size,” then built styling advice on top of that. Nothing crashed. The output just confidently said something false.

Fix: label every field on its own line — Item, Category, Colors, Style tags, Price. Whatever you leave out of the prompt, the model fills in by guessing, and a guess reads exactly like a fact.

Identical output means nothing ran

Twice I changed the prompt, reran, and got word-for-word the same answer. Both times the file hadn’t saved, so the prompt hash was unchanged and generate() served the cached response from disk. Same symptom as the pytest xfail problem in the linter: identical output before and after an edit almost always means the edit never reached the code that ran.

CACHE_ENABLED in config.py is the switch, and python -c "from generate import clear_cache; print(clear_cache())" empties it.

Grounding the model against my own data (criterion 5)

Two halves to criterion 5 and they need different mechanisms:

Say the wardrobe is empty. Putting “the wardrobe is empty” in the prompt as context wasn’t enough — the model treated it as background and never told the user. It only worked once I instructed it about the output: “start your answer by telling them that.” Context is not an instruction.
Don’t invent clothes. That rule lives in the system argument, not the prompt — the docstring in generate.py calls system “the agent’s control surface.” With the full wardrobe it named white ribbed tank, black denim jacket, chunky white sneakers and black crossbody bag — all four real items, nothing invented.

Also: wardrobe items use name, listings use title. An autocomplete suggestion used title for both and would have crashed the wardrobe branch.

Unit 4 notes — the test
Milestone 1 — moving one tool onto MCP

What MCP actually is. An agreed shape you wrap a tool in so anything speaking the same protocol can call it. Not a library, not a service — a contract. The point of moving one tool and not three is to see the seam.

What changes and what doesn’t. The call changes shape:

python
results = search_listings(desc, size, max_price)        # before
results = call_tool("search_listings", {...})           # after

The return value does not. Still a list of listing dicts, so every step after search — branch, select_item, suggest_outfit, create_fit_card — was untouched. If the return shape HAD changed, that difference would have been the first clue about what the tool was really returning before.

Three things that matter when registering a tool:

The name is the function name. def search_listings(...) under @mcp.tool() is what call_tool("search_listings", ...) asks for.
The description is the part that isn’t code and matters most. It’s written for an agent someone else builds that will never see the implementation. Name units and types (“max_price, in whole dollars” not “price”) and state the empty case — here it’s part of a published contract, not just a note to myself.
The typed inputs. FastMCP builds the input schema from the type hints, so description: str becomes a required string and max_price: float | None = None becomes an optional number. Wrong hints are the most common reason a call gets rejected.

Why the import is aliased.
from tools import search_listings as _search_listings_impl — without the alias the registered function and the one it calls would share a name and the tool would call itself.

Two things that cost me time:

Uncommenting the tool block left the ──── separator line without its #, so it became invalid Python. A SyntaxError right after uncommenting a block is almost always a comment line that lost its marker.
I pasted file contents into a bare python prompt instead of running the file. >>> and ... mean you’re in the REPL, not running a script. Ctrl+C then quit() gets out; then python mcp_client.py.
The biggest lesson of the unit: your own instrumentation can lie

The trace prints search_listings (via MCP) — but that string is hardcoded in the trace.step(...) call. _search() tries MCP and falls back to the direct call inside a bare except Exception. So if MCP were broken, the fallback would run silently and the trace would still say “via MCP.”

Seeing the label is not evidence the label is true.

I proved it by temporarily printing inside both branches:

python
try:
    results = call_tool("search_listings", {...})
    print(">>> used MCP")
except Exception as e:
    print(">>> FELL BACK to direct:", e)

>>> used MCP printed, so the claim in my README is true. Took two minutes and turned an assumption into a fact. Generalisation: a silent fallback plus a hardcoded label is a combination that can hide a broken integration forever.

Milestone 2 — breaking it on purpose

The three failures and what my agent did:

Failure	How I triggered it	What it did
Empty search	a query the data can’t match	stopped at the branch, named what to change
Empty wardrobe	--empty-wardrobe flag	suggest_outfit returned general styling advice
Model unavailable	changed one character of the key in .env	message pointing at GEMINI_API_KEY, search results kept

None of them crashed or went silent, so there was no handler to add. Don’t invent a handler for a failure that didn’t happen.

A fake pass I nearly recorded. My first empty-wardrobe run used the literal query '...' — which matches nothing, so the run died at the empty search branch and never reached suggest_outfit at all. The flag was set and the trace looked fine, but the thing I was testing never ran.

To test a failure that happens at step 4, the run has to GET to step 4. I reran with a query that returns matches plus the flag, and only then did step [4] show 0 wardrobe item(s) with real advice. Check which step the trace actually stopped at before calling a failure triggered.

The missing start_trace(). trace.py keeps _lines and _step_number at module level, and start_trace() is what resets them. run_agent() never called it. Each python app.py ask ... is a fresh process so it looked fine — but two runs in one process would keep counting [6] [7] [8] and get_trace() would return both runs glued together. Module-level state persists for the life of the process, not the life of the call.

Milestone 3 — running the test

Why five tries. My criteria are written out of five. One run can’t tell a 5-of-5 agent from a 3-of-5 agent. run_eval.py --label before runs every scenario five times with caching off.

Mapping criteria to scenarios is the actual thinking. Each criterion needs a run that exercises the thing it measures:

a branch criterion needs an impossible query
a state criterion works with any query that returns a result — what’s being checked happens inside the session, not in what the user typed
a fit-card criterion needs a query that reaches the card at all

The terminal truncates. trace.py::_short cuts strings at 110 characters, so the fit cards and outfits scroll past as "...pieces from your wardrobe:…". I nearly scored criterion 4 off that. The full text is in results/run_*.md — score from the file, never from the terminal.

Milestone 4 — calling it and diagnosing

Read the criterion plainly, not generously. My criterion said the card must have the title. The title is Suede Chelsea Boots — Tan; four of five cards said “Suede Chelsea Boots”. The generous reading (“the boots are clearly named”) gives 5 of 5. The plain reading gives 1 of 5.

The test for which reading is right: can two people score it the same way? If “the title” means “close enough to the title,” no count is possible. The strict reading produced a number and a real finding, so it’s the right one. MISSED.

A diagnosis names a place and a mechanism. Four places a failure can live: a tool, the loop’s branch, the session, or the model’s output.

Not a diagnosis: “the fit card was bad.”
A diagnosis: “the tool worked — it returned a caption with price and platform every time. The failure is the model’s output. My prompt asked for ‘the title’ but never said verbatim, while the system prompt told it to write like a person and not a product listing. Faced with an em-dash title, it resolved the tension by treating the colour suffix as droppable prose.”

Look for the pattern. The same paraphrasing was in suggest_outfit too — every outfit said “your new light wash cropped denim jacket,” never Denim Jacket — Light Wash, Cropped. Two tools, one mechanism: neither prompt demanded the exact string. Three misses on the same tool is one problem, not three.

A bug the criteria didn’t catch. On the empty-wardrobe path one caption read “I threw it over my empty wardrobe for an effortlessly cool look.” create_fit_card takes the outfit string as input; on that path the string opens “Your wardrobe is currently empty,” and the model read it as a garment. The tool worked, nothing raised — the prompt just assumed the outfit string always describes wearable items.

Revising a criterion. Allowed and earns credit only when the criterion couldn’t be measured. Lowering a target because you missed it is not a revision and costs the point. Mine was measurable, so it stayed at 4 of 5 and got a fix.

Milestone 5 — one change, measured

The change (tools.py::create_fit_card, prompt only):

before: “Include the item’s title and its price in the caption”
after: “The caption must contain the item’s title EXACTLY as written below — word for word, including everything after any dash. Do not shorten it, reword it, or drop the colour.”

Result: criterion 4 went 1/5 → 5/5. Nothing else moved.

Why one change only. I had two fixable problems (the title paraphrasing and the empty-wardrobe caption). Fixing both would make the result unattributable — no way to tell which one moved the number. The second went in What’s Still Broken.

How I know it was the change and not noise:

it generalised to items it was never tested on — the denim-jacket captions now say Denim Jacket — Light Wash, Cropped verbatim, where before every one of them said “vintage light wash cropped denim jacket”
nothing else moved, which is what should happen when one prompt is edited

The prompt fix beat the code fix. I could have added a string check with a retry loop. That raises the score without addressing why the model dropped the title. The diagnosis said the prompt was ambiguous, so the fix belongs in the prompt — follow the diagnosis, not the list of common fixes.

Don’t overclaim a side effect. The empty-wardrobe caption bug didn’t recur in the after run. It also only appeared in 1 of 5 tries before, so five clean tries is weak evidence. Wrote it up as “did not recur, not calling it fixed.”