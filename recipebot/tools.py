"""Kitchen tools database and extraction utilities."""

# Comprehensive kitchen tools database
TOOLS_DATABASE = {
    "cookware": {
        "pan",
        "pot",
        "skillet",
        "saucepan",
        "frying pan",
        "saute pan",
        "wok",
        "dutch oven",
        "stockpot",
        "casserole dish",
        "baking dish",
        "roasting pan",
        "sheet pan",
        "baking sheet",
        "cookie sheet",
        "muffin tin",
        "cake pan",
        "loaf pan",
        "pie dish",
        "tart pan",
        "ramekin",
        "souffle dish",
    },
    "utensils": {
        "whisk",
        "spatula",
        "wooden spoon",
        "ladle",
        "tongs",
        "slotted spoon",
        "serving spoon",
        "pasta fork",
        "carving fork",
        "turner",
        "fish spatula",
        "rubber spatula",
        "offset spatula",
    },
    "knives": {
        "knife",
        "chef's knife",
        "paring knife",
        "serrated knife",
        "bread knife",
        "carving knife",
        "boning knife",
        "cleaver",
    },
    "appliances": {
        "oven",
        "stove",
        "stovetop",
        "microwave",
        "toaster",
        "toaster oven",
        "mixer",
        "stand mixer",
        "hand mixer",
        "blender",
        "immersion blender",
        "food processor",
        "slow cooker",
        "pressure cooker",
        "instant pot",
        "air fryer",
        "rice cooker",
        "electric kettle",
    },
    "prep_tools": {
        "cutting board",
        "chopping board",
        "grater",
        "box grater",
        "microplane",
        "zester",
        "peeler",
        "vegetable peeler",
        "mandoline",
        "slicer",
        "colander",
        "strainer",
        "sieve",
        "fine-mesh strainer",
        "salad spinner",
        "garlic press",
        "citrus juicer",
        "can opener",
        "bottle opener",
        "corkscrew",
    },
    "measurement": {
        "measuring cup",
        "measuring spoon",
        "kitchen scale",
        "scale",
        "liquid measuring cup",
        "dry measuring cup",
    },
    "bowls": {
        "bowl",
        "mixing bowl",
        "large bowl",
        "medium bowl",
        "small bowl",
        "glass bowl",
        "metal bowl",
        "plastic bowl",
    },
    "baking": {
        "rolling pin",
        "pastry brush",
        "pastry cutter",
        "dough scraper",
        "bench scraper",
        "cookie cutter",
        "piping bag",
        "cooling rack",
        "wire rack",
        "sifter",
        "flour sifter",
    },
    "specialty": {
        "mortar and pestle",
        "meat thermometer",
        "instant-read thermometer",
        "candy thermometer",
        "kitchen timer",
        "kitchen shears",
        "poultry shears",
        "pizza cutter",
        "egg slicer",
        "melon baller",
        "ice cream scoop",
        "potato masher",
        "ricer",
    },
}

# Flatten all tools into a single set for quick lookup
ALL_TOOLS: set[str] = set()
for category in TOOLS_DATABASE.values():
    ALL_TOOLS.update(category)

# Action-to-tool inference mapping
ACTION_TO_TOOL = {
    "whisk": "whisk",
    "whisking": "whisk",
    "grate": "grater",
    "grating": "grater",
    "blend": "blender",
    "blending": "blender",
    "bake": "oven",
    "baking": "oven",
    "roast": "oven",
    "roasting": "oven",
    "sauté": "pan",
    "saute": "pan",
    "sautéing": "pan",
    "sauteing": "pan",
    "fry": "frying pan",
    "frying": "frying pan",
    "boil": "pot",
    "boiling": "pot",
    "simmer": "pot",
    "simmering": "pot",
    "mix": "mixing bowl",
    "mixing": "mixing bowl",
    "stir": "spoon",
    "stirring": "spoon",
    "chop": "knife",
    "chopping": "knife",
    "dice": "knife",
    "dicing": "knife",
    "slice": "knife",
    "slicing": "knife",
    "mince": "knife",
    "mincing": "knife",
    "peel": "peeler",
    "peeling": "peeler",
    "measure": "measuring cup",
    "measuring": "measuring cup",
    "strain": "strainer",
    "straining": "strainer",
    "drain": "colander",
    "draining": "colander",
}


def extract_tools_from_text(text: str) -> list[str]:
    """Extract kitchen tools mentioned in text.

    Args:
        text: Text to extract tools from (e.g., step description)

    Returns:
        List of identified tools
    """
    text_lower = text.lower()
    found_tools = []

    # Check for explicit tool mentions
    for tool in ALL_TOOLS:
        if tool in text_lower:
            found_tools.append(tool)

    # Infer tools from actions
    for action, tool in ACTION_TO_TOOL.items():
        if action in text_lower and tool not in found_tools:
            # Only add if not already found explicitly
            if tool not in found_tools:
                found_tools.append(tool)

    # Remove duplicates while preserving order
    seen = set()
    unique_tools = []
    for tool in found_tools:
        if tool not in seen:
            seen.add(tool)
            unique_tools.append(tool)

    return unique_tools


def get_tools_by_category(category: str) -> set[str]:
    """Get all tools in a specific category.

    Args:
        category: Category name (cookware, utensils, etc.)

    Returns:
        Set of tools in that category
    """
    return TOOLS_DATABASE.get(category, set())


if __name__ == "__main__":
    # Test examples
    test_cases = [
        "Preheat oven to 350 degrees F.",
        "Whisk together the eggs and milk in a large bowl.",
        "Sauté the onions in a pan until golden brown.",
        "Grate the cheese using a box grater.",
        "Blend all ingredients in a blender until smooth.",
        "Chop the vegetables on a cutting board.",
    ]

    print("Tool Extraction Tests:")
    print("=" * 60)
    for test in test_cases:
        tools = extract_tools_from_text(test)
        print(f"\nText: {test}")
        print(f"Tools: {', '.join(tools) if tools else 'None'}")
