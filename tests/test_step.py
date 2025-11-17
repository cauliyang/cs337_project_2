from rich import print

from recipebot.parser.step import parse_steps_from_directions


def test_step_parsing(directions, ingredients):
    print(f"Directions ({len(directions)}): {directions}")
    print(f"Ingredients ({len(ingredients)}): {ingredients}")
    steps = parse_steps_from_directions(directions, ingredients)

    for step in steps:
        print(f"\nStep {step.step_number}: {step.description}")
        print(f"  Ingredients: {[ing.name for ing in step.ingredients]}")
        print(f"  Tools: {step.tools}")
        print(f"  Methods: {step.methods}")
        print(f"  Time: {step.time}")
        print(f"  Temperature: {step.temperature}")
        print(f"  Actionable: {step.actionable}, Prepared: {step.is_prepared}")
