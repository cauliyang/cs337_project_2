import pytest
from rich.console import Console

from recipebot.crawler import scrape_recipe
from recipebot.parser import parse_steps_from_directions

console = Console()


@pytest.mark.skip(reason="This test is for reference only. It uses the recipe-scrapers library.")
def test_scraper_by_recipe(urls):
    from recipe_scrapers import scrape_me

    scraper = scrape_me(urls[0])
    console.print(scraper)
    console.print(scraper.title())
    console.print(scraper.instructions())
    console.print(scraper.to_json())


def test_scrape(urls):
    for url in urls[1:]:
        console.print(f"Testing URL: {url}")
        ingredients, directions = scrape_recipe(url)
        # Print ingredients
        console.print("Ingredients:")
        for item in ingredients:
            console.print("-", item)

        # Print directions
        console.print("\nDirections:")
        for i, step in enumerate(directions):
            console.print(f"Step {i + 1}: {step}\n")

        steps = parse_steps_from_directions(directions, ingredients, split_by_atomic_steps=True)
        console.print("Steps:")
        for step in steps:
            console.print(f"Step {step.step_number}: {step.description}")
            console.print(f"  Ingredients: {[ing.name for ing in step.ingredients]}")
            console.print(f"  Tools: {step.tools}")
            console.print(f"  Methods: {step.methods}")
            console.print(f"  Time: {step.time}")
            console.print(f"  Temperature: {step.temperature}")
            console.print(f"  Actionable: {step.actionable}, Prepared: {step.is_prepared}")
