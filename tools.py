"""
The three FitFindr tools.

Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop. Build and test them one at a time — three
untested tools joined by a loop is one problem that looks like six, because you
can't tell which layer is lying to you.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str

All three are stubs right now. They run and they do nothing — that's the
starting position and it's deliberate.

⚠️ Before you write any of them, fill in the **Tool Inventory** section of your
README (Milestone 2). Four lines per tool: what it does, each input with its
type, exactly what it returns, and what it returns when it has nothing to give.
That last line is what your loop branches on. "Returns a list" earns nothing —
the description has to say what is *in* the list.
"""

import re

import config  # noqa: F401 — you'll use this in search_listings
from generate import generate
from utils.data_loader import load_listings


_STOPWORDS = {
    "a", "an", "and", "the", "for", "with", "under", "over", "in", "of"
}


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def _keywords(text: str) -> set[str]:
    """Lowercase words worth matching on, stopwords removed."""
    words = re.findall(r"[a-z0-9']+", (text or "").lower())
    return {w for w in words if w not in _STOPWORDS and len(w) > 1}


def _size_tokens(size: str) -> set[str]:
    cleaned = re.sub(r"\([^)]*\)", " ", size or "")
    parts = [p.strip().upper() for p in re.split(r"[/\s]+", cleaned) if p.strip()]
    return {p for p in parts if p}


def _size_matches(wanted: str, listing_size: str) -> bool:
    if not wanted:
        return True

    listing_tokens = _size_tokens(listing_size)
    if any(token.startswith("ONE SIZE") for token in listing_tokens):
        return True

    wanted_tokens = _size_tokens(wanted)
    return bool(wanted_tokens & listing_tokens)


def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the listings data for items matching a description, and optionally a
    size and a price ceiling.

    This is the tool that doesn't call the model, which makes it the easiest one
    to test and the one to move onto MCP in unit 4.

    Args:
        description: keywords describing what the user wants
                     (e.g. "vintage graphic tee").
        size:        a size string to filter by, or None to skip size filtering.
                     Match case-insensitively — "M" should match "S/M".
        max_price:   maximum price, inclusive, or None to skip price filtering.

    Returns:
        A list of matching listing dicts, best match first.
        **Returns an empty list when nothing matches — an empty list, not None,
        and not an exception.** Your loop branches on this.
    """
    listings = load_listings()
    wanted_keywords = _keywords(description)
    matches: list[dict] = []

    for listing in listings:
        if max_price is not None and float(listing.get("price", 0)) > max_price:
            continue
        if size and not _size_matches(size, str(listing.get("size") or "")):
            continue

        text_blob = " ".join(
            [
                str(listing.get("title") or ""),
                str(listing.get("description") or ""),
                str(listing.get("category") or ""),
                " ".join(str(tag) for tag in (listing.get("style_tags") or [])),
                " ".join(str(color) for color in (listing.get("colors") or [])),
                str(listing.get("brand") or ""),
            ]
        )
        score = len(wanted_keywords & _keywords(text_blob))
        if score == 0:
            continue
        listing_with_score = dict(listing)
        listing_with_score["_score"] = score
        matches.append(listing_with_score)

    matches.sort(key=lambda item: item["_score"], reverse=True)
    limited = matches[: config.SEARCH_RESULT_LIMIT]
    for item in limited:
        item.pop("_score", None)
    return limited


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest one or two outfits.

    This one calls the model, through `generate()`. You don't need to think
    about rate limits — the adapter handles pacing for you.

    Args:
        new_item: a listing dict — the item the user is considering.
        wardrobe: a wardrobe dict with an 'items' key holding a list of items.
                  **It may be empty.** Handle that.

    Returns:
        A non-empty string with outfit suggestions.
        With an empty wardrobe, return general styling advice rather than
        raising or returning "". Unit 4 has you trigger the empty wardrobe on
        purpose, so decide now what it should do.
    """
    wardrobe_items = wardrobe.get("items", []) if isinstance(wardrobe, dict) else []

    if not wardrobe_items:
        prompt = (
            "Give me 2 easy outfit ideas for this thrifted item. "
            f"Item: {new_item.get('title', 'unknown item')}. "
            f"Description: {new_item.get('description', '')}. "
            f"Category: {new_item.get('category', '')}. "
            "Keep it practical, stylish, and wearable."
        )
    else:
        item_text = "\n".join(
            f"- {item.get('title', 'unknown item')} ({item.get('category', '')}, {item.get('color', '')})"
            for item in wardrobe_items
        )
        prompt = (
            "Suggest 1 or 2 outfit combinations using pieces the user already owns. "
            f"New thrifted item: {new_item.get('title', 'unknown item')} "
            f"({new_item.get('category', '')}, {new_item.get('description', '')}). "
            "Wardrobe items:\n"
            f"{item_text}\n"
            "Name the relevant existing pieces in each outfit idea."
        )

    response = generate(prompt)
    return response.strip() or "Style it with basics you already own and keep the silhouette balanced."


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Write a short caption someone would actually post about the find.

    This calls the model too.

    Args:
        outfit:   the outfit suggestion string from suggest_outfit().
        new_item: the listing dict for the item.

    Returns:
        A two-to-four sentence caption.
        If `outfit` is empty or whitespace, return a descriptive message rather
        than raising.
    """
    if not outfit or not outfit.strip():
        return (
            f"Found this {new_item.get('title', 'thrifted piece')} for "
            f"${new_item.get('price', 0):.2f} on {new_item.get('platform', 'thrift platform')} "
            f"and the vibe is effortlessly cool."
        )

    prompt = (
        "Write a catchy 2-4 sentence thrift haul caption in the first-person voice "
        "for a social post. Mention the item, its price, the platform, and the vibe. "
        f"Item: {new_item.get('title', 'unknown item')}. "
        f"Price: ${new_item.get('price', 0):.2f}. "
        f"Platform: {new_item.get('platform', 'unknown platform')}. "
        f"Outfit idea: {outfit}. "
        "Keep it natural and specific, not a product description."
    )
    response = generate(prompt)
    return response.strip() or "Found this gem for a steal and it already has my whole outfit plan mapped out."

