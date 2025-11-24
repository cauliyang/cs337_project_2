"""Cooking methods database and extraction utilities."""

from spacy.matcher import PhraseMatcher

from .spacy_utils import get_nlp

# Primary cooking methods (main techniques)
PRIMARY_METHODS = {
    # Heat-based cooking
    "bake",
    "baking",
    "roast",
    "roasting",
    "broil",
    "broiling",
    "grill",
    "grilling",
    "fry",
    "frying",
    "deep fry",
    "deep-fry",
    "pan fry",
    "pan-fry",
    "sauté",
    "saute",
    "sautéing",
    "sauteing",
    "stir-fry",
    "stir fry",
    "stir-frying",
    "boil",
    "boiling",
    "simmer",
    "simmering",
    "steam",
    "steaming",
    "poach",
    "poaching",
    "braise",
    "braising",
    "sear",
    "searing",
    "toast",
    "toasting",
    "blanch",
    "blanching",
    "caramelize",
    "caramelizing",
    # Other primary techniques
    "smoke",
    "smoking",
    "cure",
    "curing",
    "marinate",
    "marinating",
    "ferment",
    "fermenting",
}

# Words to exclude from method extraction (adjectives, particles, etc.)
METHOD_EXCLUDE_WORDS = {
    "dry",
    "wet",
    "hot",
    "cold",
    "fresh",
    "new",
    "old",
    "raw",
    "cooked",
    "large",
    "small",
    "medium",
}

# Secondary/preparation methods (supplemental actions)
SECONDARY_METHODS = {
    # Cutting techniques
    "chop",
    "chopping",
    "finely chop",
    "roughly chop",
    "coarsely chop",
    "dice",
    "dicing",
    "finely dice",
    "small dice",
    "medium dice",
    "large dice",
    "mince",
    "mincing",
    "finely mince",
    "slice",
    "slicing",
    "thinly slice",
    "thickly slice",
    "julienne",
    "julienning",
    "cube",
    "cubing",
    "cut",
    "cutting",
    "trim",
    "trimming",
    "halve",
    "halving",
    "quarter",
    "quartering",
    "shred",
    "shredding",
    "grate",
    "grating",
    "finely grate",
    "coarsely grate",
    "zest",
    "zesting",
    "peel",
    "peeling",
    "core",
    "coring",
    "pit",
    "pitting",
    "debone",
    "deboning",
    "skin",
    "skinning",
    # Mixing techniques
    "mix",
    "mixing",
    "stir",
    "stirring",
    "whisk",
    "whisking",
    "beat",
    "beating",
    "whip",
    "whipping",
    "fold",
    "folding",
    "fold in",
    "combine",
    "combining",
    "blend",
    "blending",
    "puree",
    "pureeing",
    "cream",
    "creaming",
    "knead",
    "kneading",
    "toss",
    "tossing",
    # Other preparation
    "season",
    "seasoning",
    "salt",
    "salting",
    "pepper",
    "peppering",
    "garnish",
    "garnishing",
    "coat",
    "coating",
    "dredge",
    "dredging",
    "bread",
    "breading",
    "baste",
    "basting",
    "glaze",
    "glazing",
    "brush",
    "brushing",
    "drizzle",
    "drizzling",
    "sprinkle",
    "sprinkling",
    "dust",
    "dusting",
    "pour",
    "pouring",
    "add",
    "adding",
    "incorporate",
    "divide",
    "dividing",
    "separate",
    "separating",
    "strain",
    "straining",
    "drain",
    "draining",
    "rinse",
    "rinsing",
    "wash",
    "washing",
    "dry",
    "drying",
    "pat dry",
    "squeeze",
    "squeezing",
    "press",
    "pressing",
    "crush",
    "crushing",
    "mash",
    "mashing",
    "grind",
    "grinding",
    "sift",
    "sifting",
    "roll",
    "rolling",
    "roll out",
    "shape",
    "shaping",
    "form",
    "forming",
    "flatten",
    "flattening",
    "spread",
    "spreading",
    "layer",
    "layering",
    "arrange",
    "arranging",
    "transfer",
    "transferring",
    "remove",
    "removing",
    "discard",
    "discarding",
    "reserve",
    "reserving",
    "set aside",
    "let stand",
    "let sit",
    "let rest",
    "cool",
    "cooling",
    "chill",
    "chilling",
    "refrigerate",
    "refrigerating",
    "freeze",
    "freezing",
    "thaw",
    "thawing",
    "heat",
    "heating",
    "heat up",
    "warm",
    "warming",
    "warm up",
    "preheat",
    "preheating",
    "bring to a boil",
    "bring to boil",
    "bring to a simmer",
    "reduce heat",
    "reduce",
    "reducing",
    "increase heat",
    "turn off",
    "turn off heat",
    "cover",
    "covering",
    "uncover",
    "uncovering",
}

# Combine all methods for detection
ALL_METHODS: set[str] = PRIMARY_METHODS | SECONDARY_METHODS


def extract_methods_from_text(text: str, use_spacy: bool = True) -> tuple[list[str], list[str]]:
    """Extract cooking methods from text.

    Args:
        text: Text to extract methods from (e.g., step description)
        use_spacy: Whether to use spaCy-based extraction (default: True)

    Returns:
        Tuple of (primary_methods, secondary_methods)
    """
    if use_spacy:
        return _extract_methods_with_spacy(text)
    else:
        return _extract_methods_legacy(text)


def _extract_methods_with_spacy(text: str) -> tuple[list[str], list[str]]:
    """Extract methods using spaCy's advanced matching and lemmatization.

    Args:
        text: Text to extract methods from

    Returns:
        Tuple of (primary_methods, secondary_methods)
    """
    nlp = get_nlp()
    doc = nlp(text)
    found_primary = []
    found_secondary = []
    seen_primary = set()
    seen_secondary = set()

    # Create phrase matchers
    primary_matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    secondary_matcher = PhraseMatcher(nlp.vocab, attr="LOWER")

    # Sort by length to match longer phrases first (prioritize multi-word phrases)
    sorted_primary = sorted(PRIMARY_METHODS, key=len, reverse=True)
    sorted_secondary = sorted(SECONDARY_METHODS, key=len, reverse=True)

    primary_patterns = [nlp.make_doc(method) for method in sorted_primary]
    secondary_patterns = [nlp.make_doc(method) for method in sorted_secondary]

    primary_matcher.add("PRIMARY_METHOD", primary_patterns)
    secondary_matcher.add("SECONDARY_METHOD", secondary_patterns)

    # Track spans to avoid overlapping matches
    matched_spans = set()

    # Find primary methods (longer phrases first)
    primary_matches = primary_matcher(doc)
    for _match_id, start, end in primary_matches:
        span_range = (start, end)
        # Skip if this span overlaps with already matched spans
        if any(start < e and end > s for s, e in matched_spans):
            continue

        method = doc[start:end].text.lower()
        base = _normalize_method(method)
        if base not in seen_primary and base not in METHOD_EXCLUDE_WORDS:
            found_primary.append(method)
            seen_primary.add(base)
            matched_spans.add(span_range)

    # Find secondary methods (longer phrases first)
    secondary_matches = secondary_matcher(doc)
    for _match_id, start, end in secondary_matches:
        span_range = (start, end)
        # Skip if this span overlaps with already matched spans
        if any(start < e and end > s for s, e in matched_spans):
            continue

        method = doc[start:end].text.lower()
        base = _normalize_method(method)
        # Skip if already found in primary or if it's an excluded word
        if base not in seen_secondary and base not in seen_primary and base not in METHOD_EXCLUDE_WORDS:
            found_secondary.append(method)
            seen_secondary.add(base)
            matched_spans.add(span_range)

    # Also check verb lemmas for methods (only if not already matched)
    for token in doc:
        if token.pos_ == "VERB" and token.i not in [s for s, e in matched_spans for s in range(s, e)]:
            lemma = token.lemma_
            lower = token.lower_

            # Skip excluded words
            if lemma in METHOD_EXCLUDE_WORDS or lower in METHOD_EXCLUDE_WORDS:
                continue

            # Check if verb lemma is a method
            for form in [lemma, lower]:
                if form in PRIMARY_METHODS:
                    base = _normalize_method(form)
                    if base not in seen_primary:
                        found_primary.append(form)
                        seen_primary.add(base)
                        break
                elif form in SECONDARY_METHODS:
                    base = _normalize_method(form)
                    if base not in seen_secondary and base not in seen_primary:
                        found_secondary.append(form)
                        seen_secondary.add(base)
                        break

    return found_primary, found_secondary


def _normalize_method(method: str) -> str:
    """Normalize a method name to its base form to avoid duplicates.

    Args:
        method: Method name to normalize

    Returns:
        Normalized method name
    """
    # Remove common suffixes
    base = method.lower()
    for suffix in ["ing", "e", "s"]:
        if base.endswith(suffix) and len(base) > len(suffix) + 2:
            base = base[: -len(suffix)]
    return base


def _extract_methods_legacy(text: str) -> tuple[list[str], list[str]]:
    """Legacy regex-based method extraction (fallback).

    Args:
        text: Text to extract methods from

    Returns:
        Tuple of (primary_methods, secondary_methods)
    """
    text_lower = text.lower()
    found_primary = []
    found_secondary = []

    # Check for primary methods
    for method in PRIMARY_METHODS:
        if method in text_lower:
            # Avoid duplicates (e.g., "fry" and "frying")
            base_method = method.rstrip("ing").rstrip("e")
            if base_method not in found_primary and method not in found_primary:
                found_primary.append(method)

    # Check for secondary methods
    for method in SECONDARY_METHODS:
        if method in text_lower:
            base_method = method.rstrip("ing").rstrip("e")
            if base_method not in found_secondary and method not in found_secondary:
                found_secondary.append(method)

    return found_primary, found_secondary


def get_primary_method(text: str) -> str | None:
    """Get the main primary cooking method from text.

    Args:
        text: Text to extract method from

    Returns:
        Primary method or None if not found
    """
    primary_methods, _ = extract_methods_from_text(text)
    return primary_methods[0] if primary_methods else None


def is_primary_method(method: str) -> bool:
    """Check if a method is a primary cooking method.

    Args:
        method: Method name to check

    Returns:
        True if primary method, False otherwise
    """
    return method.lower() in PRIMARY_METHODS


def is_secondary_method(method: str) -> bool:
    """Check if a method is a secondary/preparation method.

    Args:
        method: Method name to check

    Returns:
        True if secondary method, False otherwise
    """
    return method.lower() in SECONDARY_METHODS
