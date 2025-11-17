"""Step parser for converting raw directions into structured steps."""

import re
from typing import Literal

from recipebot.model import Ingredient, Step

from .methods import extract_methods_from_text
from .tools import extract_tools_from_text

# Regular expressions for time extraction
TIME_PATTERNS = [
    re.compile(
        r"(\d+(?:\.\d+)?)\s*(?:to|\-)\s*(\d+(?:\.\d+)?)\s*(hour|hr|minute|min|second|sec)s?", flags=re.IGNORECASE
    ),  # "2-3 hours"
    re.compile(r"(\d+(?:\.\d+)?)\s*(hour|hr|minute|min|second|sec)s?", flags=re.IGNORECASE),  # "30 minutes"
    re.compile(r"for\s+(\d+(?:\.\d+)?)\s*(hour|hr|minute|min|second|sec)s?", flags=re.IGNORECASE),  # "for 30 minutes"
]

# Regular expressions for temperature extraction
TEMP_PATTERNS = [
    re.compile(r"(\d+)\s*(?:degrees?|°)\s*([FC])", flags=re.IGNORECASE),  # "350 degrees F" or "350°F"
    re.compile(r"(\d+)\s*([FC])", flags=re.IGNORECASE),  # "350F"
    re.compile(r"(low|medium|high|medium-low|medium-high)\s+heat", flags=re.IGNORECASE),  # "medium heat"
]

# Sentence splitting patterns
SENTENCE_SPLITTERS = [
    re.compile(r"\.\s+[A-Z]", flags=re.IGNORECASE),  # Period followed by capital letter
    re.compile(r";\s*", flags=re.IGNORECASE),  # Semicolon
    re.compile(r",\s+then\s+", flags=re.IGNORECASE),  # ", then "
    re.compile(r",\s+and then\s+", flags=re.IGNORECASE),  # ", and then "
    re.compile(r"\s+meanwhile\s+", flags=re.IGNORECASE),  # " meanwhile "
    re.compile(r"\s+while\s+", flags=re.IGNORECASE),  # " while "
]


def extract_time_from_text(text: str) -> dict[str, str | int]:
    """Extract time/duration information from text.

    Args:
        text: Text to extract time from

    Returns:
        Dictionary with time information
    """
    time_info = {}
    text_lower = text.lower()

    # Check for range patterns first (e.g., "2-3 hours")
    range_match = re.search(TIME_PATTERNS[0], text_lower)
    if range_match:
        min_val, max_val, unit = range_match.groups()
        time_info["duration_min"] = int(float(min_val))
        time_info["duration_max"] = int(float(max_val))
        time_info["unit"] = unit
        return time_info

    # Check for single value patterns
    for pattern in TIME_PATTERNS[1:]:
        match = re.search(pattern, text_lower)
        if match:
            if len(match.groups()) == 2:
                value, unit = match.groups()
                time_info["duration"] = int(float(value))
                time_info["unit"] = unit
            return time_info

    # Check for qualitative time descriptions
    qualitative_patterns = [
        re.compile(r"until\s+(golden|brown|soft|tender|translucent|cooked|done)", flags=re.IGNORECASE),
        re.compile(r"until\s+(.+?)\s+(?:is|are)", flags=re.IGNORECASE),
    ]

    for pattern in qualitative_patterns:
        match = re.search(pattern, text_lower)
        if match:
            time_info["duration"] = match.group(0)
            time_info["type"] = "qualitative"
            return time_info

    return time_info


def extract_temperature_from_text(text: str) -> dict[str, str]:
    """Extract temperature information from text.

    Args:
        text: Text to extract temperature from

    Returns:
        Dictionary with temperature information
    """
    temp_info = {}

    # Check for numeric temperature patterns
    for pattern in TEMP_PATTERNS[:3]:
        match = re.search(pattern, text.lower())
        if match:
            if len(match.groups()) == 2:
                temp, unit = match.groups()
                if unit.upper() in ["F", "C"]:
                    temp_info["oven"] = f"{temp}°{unit.upper()}"
                else:
                    # Qualitative (low, medium, high)
                    temp_info["heat"] = match.group(0)
            return temp_info

    # Check for preheat references
    preheat_match = re.search(r"preheat.*?(\d+)\s*°?\s*([FC])?", text.lower())
    if preheat_match:
        temp = preheat_match.group(1)
        unit = preheat_match.group(2) or "F"
        temp_info["oven"] = f"{temp}°{unit.upper()}"

    return temp_info


def split_into_atomic_steps(direction: str) -> list[str]:
    """Split a complex direction into atomic steps.

    Args:
        direction: Single direction text

    Returns:
        List of atomic step descriptions
    """
    # First, try to split by common patterns
    steps = [direction]

    # Split by sentence boundaries with conjunctions
    for splitter in SENTENCE_SPLITTERS:
        new_steps = []
        for step in steps:
            # Find all split points
            parts = re.split(splitter, step)
            new_steps.extend([p.strip() for p in parts if p.strip()])
        steps = new_steps

    # Clean up steps
    cleaned_steps = []
    for step in steps:
        # Remove leading conjunctions
        step = re.sub(r"^(then|and|meanwhile|while)\s+", "", step, flags=re.IGNORECASE)
        # Ensure first letter is capitalized
        if step:
            step = step[0].upper() + step[1:]
            cleaned_steps.append(step)

    return cleaned_steps if cleaned_steps else [direction]


def classify_step_type(text: str) -> tuple[bool, bool, Literal["warning", "advice", "observation"] | None]:
    """Classify step as actionable, preparatory, or informational.

    Args:
        text: Step description

    Returns:
        Tuple of (actionable, is_prepared, info_type)
    """
    text_lower = text.lower()

    # Check for warnings
    warning_patterns = ["be careful", "do not", "don't", "avoid", "make sure", "watch", "be sure", "ensure"]
    for pattern in warning_patterns:
        if pattern in text_lower:
            return (True, False, "warning")

    # Check for advice
    advice_patterns = ["you can", "alternatively", "tip:", "note:", "optional", "if desired", "for best results"]
    for pattern in advice_patterns:
        if pattern in text_lower:
            return (False, False, "advice")

    # Check for observations
    observation_patterns = [
        "will be",
        "should be",
        "will look",
        "should look",
        "will become",
        "it will",
        "this will",
        "the mixture will",
    ]
    for pattern in observation_patterns:
        if pattern in text_lower:
            return (False, False, "observation")

    # Check if preparatory (for future steps)
    prep_patterns = [
        "set aside",
        "reserve",
        "let stand",
        "let sit",
        "let rest",
        "let cool",
        "refrigerate",
        "chill",
        "freeze",
    ]
    is_prepared = any(pattern in text_lower for pattern in prep_patterns)

    # Default: actionable
    return (True, is_prepared, None)


def extract_ingredients_from_step(step_text: str, all_ingredients: list[Ingredient]) -> list[Ingredient]:
    """Find which ingredients from the recipe are mentioned in this step.

    Args:
        step_text: Step description
        all_ingredients: List of all ingredients in recipe

    Returns:
        List of ingredients used in this step
    """
    step_text_lower = step_text.lower()
    found_ingredients = []

    for ingredient in all_ingredients:
        # Check for ingredient name or variations
        name_lower = ingredient.name.lower()

        # Direct match
        if name_lower in step_text_lower:
            found_ingredients.append(ingredient)
            continue

        # Check with "the" prefix
        if f"the {name_lower}" in step_text_lower:
            found_ingredients.append(ingredient)
            continue

        # Check for plural forms
        if f"{name_lower}s" in step_text_lower:
            found_ingredients.append(ingredient)
            continue

        # Check for partial matches (e.g., "chicken" in "chicken breast")
        name_parts = name_lower.split()
        if any(part in step_text_lower for part in name_parts if len(part) > 3):
            found_ingredients.append(ingredient)

    return found_ingredients


def parse_steps_from_directions(
    directions: list[str],
    all_ingredients: list[Ingredient],
    context: dict | None = None,
    split_by_atomic_steps: bool = True,
) -> list[Step]:
    """Parse directions into structured steps with full metadata.

    Args:
        directions: List of direction strings
        all_ingredients: List of ingredients in recipe
        context: Optional context to carry forward (e.g., oven temperature)

    Returns:
        List of parsed Step objects
    """
    if context is None:
        context = {}

    steps = []
    step_number = 1

    for direction in directions:
        # Split into atomic steps if needed
        atomic_steps = split_into_atomic_steps(direction) if split_by_atomic_steps else [direction]

        for atomic_step in atomic_steps:
            # Extract all metadata
            tools = extract_tools_from_text(atomic_step)
            primary_methods, secondary_methods = extract_methods_from_text(atomic_step)
            all_methods = primary_methods + secondary_methods

            time_info = extract_time_from_text(atomic_step)
            temp_info = extract_temperature_from_text(atomic_step)

            # Carry forward oven temperature from context if baking/roasting
            if any(method in ["bake", "baking", "roast", "roasting"] for method in primary_methods):
                if "oven" not in temp_info and "oven_temp" in context:
                    temp_info["oven"] = context["oven_temp"]

            # Update context with new temperature
            if "oven" in temp_info:
                context["oven_temp"] = temp_info["oven"]

            # Classify step
            actionable, is_prepared, info_type = classify_step_type(atomic_step)

            # Find ingredients mentioned in this step
            step_ingredients = extract_ingredients_from_step(atomic_step, all_ingredients)

            # Create Step object
            step = Step(
                step_number=step_number,
                description=atomic_step,
                ingredients=step_ingredients,
                tools=tools,
                methods=all_methods,
                time=time_info,
                temperature=temp_info,
                actionable=actionable,
                is_prepared=is_prepared,
                info_type=info_type,
            )

            steps.append(step)
            step_number += 1

    return steps


if __name__ == "__main__":
    from rich import print

    # Test examples
    test_directions = [
        "Preheat oven to 350 degrees F (175 degrees C).",
        "In a large bowl, whisk together the flour, sugar, and salt.",
        "Sauté the onions in a pan over medium heat for 5-7 minutes, stirring occasionally, until golden brown.",
        "Bake for 30 minutes or until golden. Let cool before serving.",
        "Be careful not to overmix the batter.",
        "You can substitute butter for oil if desired.",
    ]
    # Mock ingredients
    mock_ingredients = [
        Ingredient(name="flour", quantity="2", unit="cups"),
        Ingredient(name="sugar", quantity="1", unit="cup"),
        Ingredient(name="salt", quantity="1", unit="teaspoon"),
        Ingredient(name="onions", quantity="2", unit=None),
        Ingredient(name="butter", quantity="1/2", unit="cup"),
    ]

    print("Step Parsing Tests:")
    print("=" * 80)

    steps = parse_steps_from_directions(test_directions, mock_ingredients)

    for step in steps:
        print(f"\nStep {step.step_number}: {step.description}")
        print(f"  Ingredients: {[ing.name for ing in step.ingredients]}")
        print(f"  Tools: {step.tools}")
        print(f"  Methods: {step.methods}")
        print(f"  Time: {step.time}")
        print(f"  Temperature: {step.temperature}")
        print(f"  Actionable: {step.actionable}, Prepared: {step.is_prepared}")
