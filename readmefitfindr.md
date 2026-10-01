## How I got to my criteria (Milestone 3)

The rule I used: a criterion has to be checkable by looking at the output, not by
judging whether it reads well. "The outfit suggestion is good" can't be scored.
"The names it mentions appear in the wardrobe I passed in" can.

Then the target depends on how much room the model has to be right in different
words:

- **5 of 5 for things that are either right or wrong.** The returned id either
  matches the item the loop forwarded or it doesn't — there's no phrasing
  involved, so anything under 5 of 5 is a real defect, not variance. Same for
  wardrobe items: either the name is in the wardrobe or the model made it up.
- **4 of 5 where the model can legitimately phrase it differently.** The fit card
  has to contain the price and the title, but titles are long and a caption that
  drops a word or two from one is still doing its job. Price and title aren't
  equally fragile, so demanding 5 of 5 would fail runs that are actually fine.

The reason behind each one is the same question: what goes wrong for the user if
this fails? A wrong id means the agent recommended an outfit for an item the user
never asked about, and nothing in the output would reveal it. Naming a wardrobe
item the user doesn't own is a false claim about their own data. Those are worth
a strict target. A caption that's slightly loose with wording isn't.

# Milestone 4 notes — building the tools

## The tools were stubs
All three functions in tools.py had `return []` as their whole body. Every empty
result I got was correct behavior for a function that does nothing. When a
function returns nothing for every input, read the body before testing more
inputs.

## Bugs already in the starter
- `import re` was missing — _keywords would crash the moment it ran.
- `_size_tokens` had `p.strip().upper` with no parentheses, so the set filled
  with method objects instead of strings. The error surfaced three functions
  away. Same mistake as `return bool` instead of `return True` in the linter.

## Python things I got wrong
- `and` evaluates left to right, so the None guard has to go on the left or the
  comparison crashes before the guard is reached.
- Every `continue` has to come before the append, or it can't prevent anything.
- Never remove from a list you're looping over — removing shifts everything left
  while the loop moves right, so it silently skips items.
- To sort by score, append `(score, listing)` pairs so the score survives the
  loop, sort with `key=lambda x: x[0], reverse=True`, then strip the scores off
  and slice to config.SEARCH_RESULT_LIMIT (10).

## What this means for my criteria

**Criterion 1 — the returned id must be the right item.**
Keyword overlap can't tell what an item IS from what it MENTIONS. Searching
"graphic tee" returns lst_017, a black mesh top, because its description says
"great for layering under a graphic tee." Matching on `description` alone it
scored 2 — tied with lst_002, the real baby tee. A tie means the wrong item
could come out first, and the loop hands the first result to suggest_outfit.

I widened the match to title + description + style_tags. Now lst_002 ranks first
and lst_017 third. The false positive is still in the results, it just no longer
wins — scoring across more fields rewards items that ARE the thing over items
that mention it.

Still a risk: nothing stops a future query from tying again. Criterion 1 is
testing exactly this, so if it misses, the diagnosis is the scoring, not the loop.

**Criterion 5 — empty wardrobe must say so rather than invent items.**
get_empty_wardrobe() in utils/data_loader.py returns the empty case already
built, so I can trigger it on purpose instead of constructing one by hand.

## suggest_outfit — what the model does with a sloppy prompt

My first prompt put the price in bare parentheses: `{title} ({price})`. The model
read 38.0 as a measurement and wrote "because they are a 38-inch size," then built
styling advice on top of that. Nothing crashed. The output just confidently said
something false.

Fix: label every field on its own line — Item, Category, Colors, Style tags,
Price. Whatever you leave out of the prompt, the model fills in by guessing, and
a guess reads exactly like a fact.

## Identical output means nothing ran

Twice I changed the prompt, reran, and got word-for-word the same answer. Both
times the file hadn't saved, so the prompt hash was unchanged and generate()
served the cached response from disk. Same symptom as the pytest xfail problem in
the linter: identical output before and after an edit almost always means the
edit never reached the code that ran.

CACHE_ENABLED in config.py is the switch, and
`python -c "from generate import clear_cache; print(clear_cache())"` empties it.

## Grounding the model against my own data (criterion 5)

Two halves to criterion 5 and they need different mechanisms:

- **Say the wardrobe is empty.** Putting "the wardrobe is empty" in the prompt as
  context wasn't enough — the model treated it as background and never told the
  user. It only worked once I instructed it about the *output*: "start your answer
  by telling them that." Context is not an instruction.
- **Don't invent clothes.** That rule lives in the `system` argument, not the
  prompt — the docstring in generate.py calls system "the agent's control
  surface." With the full wardrobe it named white ribbed tank, black denim jacket,
  chunky white sneakers and black crossbody bag — all four real items, nothing
  invented.

Also: wardrobe items use `name`, listings use `title`. An autocomplete suggestion
used `title` for both and would have crashed the wardrobe branch.