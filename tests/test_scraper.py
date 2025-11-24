import pytest
from rich.console import Console

from recipebot.parser import parse_recipe, show_recipe

console = Console()


@pytest.mark.skip(reason="This test is for reference only. It uses the recipe-scrapers library.")
def test_scraper_by_recipe(allrecipes_url, seriouseats_url):
    from recipe_scrapers import scrape_me

    scraper = scrape_me(allrecipes_url[0])
    console.print(scraper)
    console.print(scraper.title())
    console.print(scraper.instructions())
    console.print(scraper.to_json())


def test_scrape(allrecipes_url, seriouseats_url):
    for url in allrecipes_url + seriouseats_url:
        recipe = parse_recipe(url, split_by_atomic_steps=True)
        console.print(recipe.directions)
        show_recipe(recipe)
