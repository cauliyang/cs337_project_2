import pytest
from rich import print

from recipebot.crawler import scrape_recipe


@pytest.fixture
def urls():
    return ["https://www.allrecipes.com/recipe/24074/alysias-basic-meat-lasagna/"]


def test_scraper_by_recipe(urls):
    from recipe_scrapers import scrape_me

    scraper = scrape_me(urls[0])
    print(scraper)
    print(scraper.title())
    print(scraper.instructions())
    print(scraper.to_json())


def test_scrape(urls):
    for url in urls:
        print(f"Testing URL: {url}")
        ingredients, directions = scrape_recipe(url)
        # Print ingredients
        print("Ingredients:")
        for item in ingredients:
            print("-", item)

        # Print directions
        print("\nDirections:")
        for i, step in enumerate(directions):
            print(f"Step {i + 1}: {step}\n")
