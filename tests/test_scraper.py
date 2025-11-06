import pytest

from recipebot.crawler import scrape_allrecipes, scrape_recipe


@pytest.fixture
def urls():
    return ["https://www.allrecipes.com/recipe/24074/alysias-basic-meat-lasagna/"]


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


def test_scrape_allrecipes(urls):
    for url in urls:
        print(f"Testing AllRecipes URL: {url}")
        ingredients, directions = scrape_allrecipes(url)
        print("Ingredients:")
        for item in ingredients:
            print("-", item)

        print("\nDirections:")
        for i, step in enumerate(directions):
            print(f"Step {i + 1}: {step}\n")
