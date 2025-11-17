from rich import print

from recipebot.parser import extract_methods_from_text


def test_method_extraction(directions):
    for test in directions:
        primary, secondary = extract_methods_from_text(test)
        print(f"\nText: {test}")
        print(f"Primary: {', '.join(primary) if primary else 'None'}")
        print(f"Secondary: {', '.join(secondary) if secondary else 'None'}")
