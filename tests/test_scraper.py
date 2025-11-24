import pytest
from rich.console import Console

from recipebot.parser import parse_recipe, show_recipe


@pytest.mark.skip(reason="This test is for reference only. It uses the recipe-scrapers library.")
def test_scraper_by_recipe(urls):
    from recipe_scrapers import scrape_me

    console = Console()

    scraper = scrape_me(urls[0])
    console.print(scraper)
    console.print(scraper.title())
    console.print(scraper.instructions())
    console.print(scraper.to_json())


def test_scrape(allrecipes_url, seriouseats_url):
    for url in allrecipes_url:
        recipe = parse_recipe(url, split_by_atomic_steps=False)
        show_recipe(recipe)
