"""Recipe parser that fetches and parses recipes from URLs."""

from recipebot.crawler import extract_title_from_url, scrape_recipe
from recipebot.model import Recipe

from .step import parse_steps_from_directions


def parse_recipe(url: str) -> Recipe:
    """Fetch and parse recipe from URL.

    Returns:
        Parsed Recipe object with ingredients, directions, and steps

    Raises
        ValueError: If URL is invalid or recipe cannot be parsed
        requests.HTTPError: If HTTP request fails
    """
    # Fetch raw recipe data
    ingredients, directions = scrape_recipe(url)
    if not ingredients or not directions:
        raise ValueError(f"Failed to parse recipe from {url}")

    title = extract_title_from_url(url)
    # Parse steps with full metadata
    steps = parse_steps_from_directions(directions, ingredients)

    # Create Recipe object
    recipe = Recipe(
        title=title,
        ingredients=ingredients,
        directions=directions,
        steps=steps,
    )

    return recipe
