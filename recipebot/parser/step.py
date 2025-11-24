"""Step parser for converting raw directions into structured steps."""

import re
from typing import Literal

from recipebot.model import Ingredient, Step

from .methods import extract_methods_from_text
from .spacy_utils import (
    create_temperature_matcher,
    create_time_matcher,
    extract_temperature_with_spacy,
    extract_time_with_spacy,
    get_nlp,
    is_imperative_sentence,
    match_ingredient_with_spacy,
    split_into_sentences_with_spacy,
)
from .tools import extract_tools_from_text

# Regular expressions for time extraction
TIME_PATTERNS = [
    re.compile(
        r"(\d+(?:\.\d+)?)\s*(?:to|\-)\s*(\d+(?:\.\d+)?)\s*(hour|hr|hours|hrs|minute|min|minutes|mins|second|sec|seconds|secs)s?", flags=re.IGNORECASE
    ),  # "2-3 hours"
    re.compile(r"(?:about|approximately|around|for)\s+(\d+(?:\.\d+)?)\s*(hour|hr|hours|hrs|minute|min|minutes|mins|second|sec|seconds|secs)s?", flags=re.IGNORECASE),  # "about 1 hour", "for 30 minutes"
    re.compile(r"(\d+(?:\.\d+)?)\s*(hour|hr|hours|hrs|minute|min|minutes|mins|second|sec|seconds|secs)s?", flags=re.IGNORECASE),  # "30 minutes", "1 hour"
]

# Regular expressions for temperature extraction
TEMP_PATTERNS = [
    re.compile(r"(\d+)\s*(?:degrees?|°)\s*([FC])", flags=re.IGNORECASE),  # "350 degrees F" or "350°F"
    re.compile(r"(\d+)\s*([FC])", flags=re.IGNORECASE),  # "350F"
    re.compile(r"(low|medium|high|medium-low|medium-high)\s+heat", flags=re.IGNORECASE),  # "medium heat"
]

# Sentence splitting patterns
SENTENCE_SPLITTERS = [
    re.compile(r"\.\s+(?=[A-Z])", flags=re.IGNORECASE),  # Period followed by capital letter (lookahead)
    re.compile(r";\s*", flags=re.IGNORECASE),  # Semicolon
    re.compile(r",\s+then\s+", flags=re.IGNORECASE),  # ", then "
    re.compile(r",\s+and then\s+", flags=re.IGNORECASE),  # ", and then "
    re.compile(r"\s+meanwhile\s+", flags=re.IGNORECASE),  # " meanwhile "
    re.compile(r"\s+while\s+", flags=re.IGNORECASE),  # " while "
]


def extract_time_from_text(text: str, use_spacy: bool = True) -> dict[str, str | int]:
    """Extract time/duration information from text.

    Args:
        text: Text to extract time from
        use_spacy: Whether to use spaCy-based extraction (default: True)

    Returns:
        Dictionary with time information
    """
    if use_spacy:
        nlp = get_nlp()
        doc = nlp(text)
        time_matcher = create_time_matcher(nlp)
        spacy_time_info = extract_time_with_spacy(doc, time_matcher)
        if spacy_time_info:
            return spacy_time_info
        # Fall back to regex if spaCy doesn't find anything

    # Legacy regex-based extraction
    time_info: dict[str, str | int] = {}
    text_lower = text.lower()

    # Normalize unit to singular form for consistent storage
    def normalize_unit_to_singular(unit: str) -> str:
        """Normalize unit to singular form."""
        if not unit:
            return "minute"
        unit_lower = unit.lower()
        # Map to singular forms
        if unit_lower in ["hour", "hours", "hr", "hrs", "h"]:
            return "hour"
        elif unit_lower in ["minute", "minutes", "min", "mins", "m"]:
            return "minute"
        elif unit_lower in ["second", "seconds", "sec", "secs", "s"]:
            return "second"
        return unit_lower

    # Check for range patterns first (e.g., "2-3 hours")
    range_match = re.search(TIME_PATTERNS[0], text_lower)
    if range_match:
        min_val, max_val, unit = range_match.groups()
        time_info["duration_min"] = int(float(min_val))
        time_info["duration_max"] = int(float(max_val))
        time_info["unit"] = normalize_unit_to_singular(unit)
        return time_info

    # Check for single value patterns
    for pattern in TIME_PATTERNS[1:]:
        match = re.search(pattern, text_lower)
        if match:
            if len(match.groups()) == 2:
                value, unit = match.groups()
                time_info["duration"] = int(float(value))
                time_info["unit"] = normalize_unit_to_singular(unit)
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


def extract_temperature_from_text(text: str, use_spacy: bool = True) -> dict[str, str]:
    """Extract temperature information from text.

    Args:
        text: Text to extract temperature from
        use_spacy: Whether to use spaCy-based extraction (default: True)

    Returns:
        Dictionary with temperature information
    """
    if use_spacy:
        nlp = get_nlp()
        doc = nlp(text)
        temp_matcher = create_temperature_matcher(nlp)
        spacy_temp_info = extract_temperature_with_spacy(doc, temp_matcher)
        if spacy_temp_info:
            return spacy_temp_info
        # Fall back to regex if spaCy doesn't find anything

    # Legacy regex-based extraction
    temp_info: dict[str, str] = {}

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


def split_into_atomic_steps(direction: str, use_spacy: bool = True) -> list[str]:
    """Split a complex direction into atomic steps.

    Args:
        direction: Single direction text
        use_spacy: Whether to use spaCy-based splitting (default: True)

    Returns:
        List of atomic step descriptions
    """
    if use_spacy:
        nlp = get_nlp()
        sentences = split_into_sentences_with_spacy(direction, nlp)

        # Clean up steps
        cleaned_steps = []
        for step in sentences:
            # Remove leading conjunctions
            step = re.sub(r"^(then|and|meanwhile|while)\s+", "", step, flags=re.IGNORECASE)
            # Ensure first letter is capitalized
            if step:
                step = step[0].upper() + step[1:]
                cleaned_steps.append(step)

        return cleaned_steps if cleaned_steps else [direction]

    # Legacy regex-based splitting
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


def classify_step_type(
    text: str, use_spacy: bool = True
) -> tuple[bool, bool, Literal["warning", "advice", "observation"] | None]:
    """Classify step as actionable, preparatory, or informational.

    Args:
        text: Step description
        use_spacy: Whether to use spaCy-based classification (default: True)

    Returns:
        Tuple of (actionable, is_prepared, info_type)
    """
    text_lower = text.lower()

    # Enhanced classification using spaCy
    if use_spacy:
        nlp = get_nlp()
        doc = nlp(text)

        # Check if it's an imperative sentence (command) -> more likely actionable
        _is_imperative = is_imperative_sentence(doc)

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

    # Check for observations (using spaCy for better detection)
    if use_spacy:
        nlp = get_nlp()
        doc = nlp(text)
        # Look for future tense patterns
        for token in doc:
            if token.tag_ in ["MD"] and token.lower_ in ["will", "should"]:  # Modal verbs
                # Check if followed by "be", "look", "become"
                for child in token.children:
                    if child.lemma_ in ["be", "look", "become"]:
                        return (False, False, "observation")

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


def extract_ingredients_from_step(
    step_text: str, all_ingredients: list[Ingredient], use_spacy: bool = True
) -> list[Ingredient]:
    """Find which ingredients from the recipe are mentioned in this step.

    Args:
        step_text: Step description
        all_ingredients: List of all ingredients in recipe
        use_spacy: Whether to use spaCy-based matching (default: True)

    Returns:
        List of ingredients used in this step
    """
    if use_spacy:
        nlp = get_nlp()
        doc = nlp(step_text)
        found_ingredients = []

        for ingredient in all_ingredients:
            # Handle potential None values for ingredient.name
            if ingredient.name is not None and match_ingredient_with_spacy(ingredient.name, doc, nlp):
                found_ingredients.append(ingredient)

        return found_ingredients

    # Legacy string-based matching
    step_text_lower = step_text.lower()
    found_ingredients = []

    for ingredient in all_ingredients:
        # Handle potential None values for ingredient.name
        if ingredient.name is None:
            continue

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
    use_spacy: bool = True,
) -> list[Step]:
    """Parse directions into structured steps with full metadata.

    Args:
        directions: List of direction strings
        all_ingredients: List of ingredients in recipe
        context: Optional context to carry forward (e.g., oven temperature)
        split_by_atomic_steps: Whether to split complex directions into atomic steps
        use_spacy: Whether to use spaCy-based parsing (default: True)

    Returns:
        List of parsed Step objects
    """
    if context is None:
        context = {}

    steps = []
    step_number = 1

    for direction in directions:
        # Split into atomic steps if needed
        atomic_steps = split_into_atomic_steps(direction, use_spacy=use_spacy) if split_by_atomic_steps else [direction]

        for atomic_step in atomic_steps:
            # Extract all metadata using spaCy-enhanced functions
            tools = extract_tools_from_text(atomic_step, use_spacy=use_spacy)
            primary_methods, secondary_methods = extract_methods_from_text(atomic_step, use_spacy=use_spacy)
            all_methods = primary_methods + secondary_methods

            time_info = extract_time_from_text(atomic_step, use_spacy=use_spacy)
            temp_info = extract_temperature_from_text(atomic_step, use_spacy=use_spacy)

            # Carry forward oven temperature from context if baking/roasting
            if any(method in ["bake", "baking", "roast", "roasting"] for method in primary_methods):
                if "oven" not in temp_info and "oven_temp" in context:
                    temp_info["oven"] = context["oven_temp"]

            # Update context with new temperature
            if "oven" in temp_info:
                context["oven_temp"] = temp_info["oven"]

            # Classify step
            actionable, is_prepared, info_type = classify_step_type(atomic_step, use_spacy=use_spacy)

            # Find ingredients mentioned in this step
            step_ingredients = extract_ingredients_from_step(atomic_step, all_ingredients, use_spacy=use_spacy)

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
