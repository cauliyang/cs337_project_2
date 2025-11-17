"""Cooking methods database and extraction utilities."""

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
    "reduce",
    "reducing",
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


def extract_methods_from_text(text: str) -> tuple[list[str], list[str]]:
    """Extract cooking methods from text.

    Args:
        text: Text to extract methods from (e.g., step description)

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


if __name__ == "__main__":
    # Test examples
    test_cases = [
        "Preheat the oven to 375 degrees F (190 degrees C).",
        "Make the sauce: Heat oil in a large saucepan over medium-high heat. Add onion and garlic; cook and stir until translucent, about 5 minutes. Add ground beef and garlic powder; cook and stir until browned and crumbly, 5 to 7 minutes. Drain and discard grease.  Add spaghetti sauce, tomato sauce, and oregano; cover and simmer for 15 to 20 minutes.",  # noqa: E501
        "Make the lasagna: Mix mozzarella and provolone together in a medium bowl. Mix ricotta, milk, eggs, and oregano together in another bowl.",  # noqa: E501
        "Ladle sauce (just enough to cover) into the bottom of a 9x13-inch baking dish.  Layer sauce with three lasagna noodles, more sauce, ricotta mixture, and mozzarella mixture; repeat once more using all of remaining cheese mixtures. Layer with remaining three lasagna noodles and remaining sauce, then sprinkle Parmesan over top.",  # noqa: E501
        "Cover and bake in the preheated oven for 30 minutes. Uncover and continue to bake until cheese is melted and top is golden, about 15 minutes longer.",  # noqa: E501
    ]

    print("Method Extraction Tests:")
    print("=" * 60)
    for test in test_cases:
        primary, secondary = extract_methods_from_text(test)
        print(f"\nText: {test}")
        print(f"Primary: {', '.join(primary) if primary else 'None'}")
        print(f"Secondary: {', '.join(secondary) if secondary else 'None'}")
