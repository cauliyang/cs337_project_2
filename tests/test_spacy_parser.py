#!/usr/bin/env python3
"""Test suite for spaCy-based parsing optimizations."""

from rich import print

from recipebot.parser import methods, step, tools


def test_time_extraction():
    """Test time extraction with spaCy."""

    test_cases = [
        "Bake for 30 minutes until golden brown",
        "Cook for 2-3 hours on low heat",
        "Simmer for 45 minutes",
        "Let rest for 10 mins",
        "Bake until tender and cooked through",
    ]

    for text in test_cases:
        result = step.extract_time_from_text(text, use_spacy=True)
        print(f"Text: {text}")
        print(f"  Result: {result}")


def test_temperature_extraction():
    """Test temperature extraction with spaCy."""
    test_cases = [
        "Preheat oven to 350°F",
        "Bake at 180 degrees C",
        "Cook over medium heat",
        "Heat to 400F",
        "Roast at high heat",
    ]

    for text in test_cases:
        result = step.extract_temperature_from_text(text, use_spacy=True)
        print(f"Text: {text}")
        print(f"  Result: {result}")


def test_tool_extraction():
    """Test tool extraction with spaCy."""
    test_cases = [
        "Mix ingredients in a large mixing bowl",
        "Heat oil in a skillet over medium heat",
        "Whisk eggs until frothy",
        "Chop onions with a sharp knife",
        "Bake in the oven at 350F",
        "Blend until smooth using an immersion blender",
    ]

    for text in test_cases:
        result = tools.extract_tools_from_text(text, use_spacy=True)
        print(f"Text: {text}")
        print(f"  Tools: {result}")


def test_method_extraction():
    """Test cooking method extraction with spaCy."""
    test_cases = [
        "Sauté onions until translucent, then add garlic",
        "Mix dry ingredients and whisk together",
        "Bake for 30 minutes, then reduce heat and continue baking",
        "Chop vegetables, dice tomatoes, and mince garlic",
        "Boil water, add pasta, and simmer for 10 minutes",
    ]

    for text in test_cases:
        primary, secondary = methods.extract_methods_from_text(text, use_spacy=True)
        print(f"Text: {text}")
        print(f"  Primary: {primary}")
        print(f"  Secondary: {secondary}")


def test_comparison():
    """Compare spaCy vs legacy extraction."""
    text = "Sauté onions in a large skillet for 5-7 minutes until golden, then add garlic and cook for 2 more minutes."

    print(f"\nTest text: {text}\n")

    # Tools
    print("Tools:")
    tools_spacy = tools.extract_tools_from_text(text, use_spacy=True)
    tools_legacy = tools.extract_tools_from_text(text, use_spacy=False)
    print(f"  spaCy:  {tools_spacy}")
    print(f"  Legacy: {tools_legacy}")

    # Methods
    print("\nMethods:")
    primary_s, secondary_s = methods.extract_methods_from_text(text, use_spacy=True)
    primary_l, secondary_l = methods.extract_methods_from_text(text, use_spacy=False)
    print(f"  spaCy Primary:  {primary_s}")
    print(f"  Legacy Primary: {primary_l}")
    print(f"  spaCy Secondary:  {secondary_s}")
    print(f"  Legacy Secondary: {secondary_l}")

    # Time
    print("\nTime:")
    time_spacy = step.extract_time_from_text(text, use_spacy=True)
    time_legacy = step.extract_time_from_text(text, use_spacy=False)
    print(f"  spaCy:  {time_spacy}")
    print(f"  Legacy: {time_legacy}")
