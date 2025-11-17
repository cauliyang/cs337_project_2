import requests
from bs4 import BeautifulSoup

from recipebot.model import Ingredient


def extract_title_from_url(url: str) -> str:
    """Extract recipe title from URL."""
    # Extract last part of URL path and clean it up
    path_parts = url.rstrip("/").split("/")
    # Find the recipe name (usually after 'recipe/')
    for i, part in enumerate(path_parts):
        if part == "recipe" and i + 1 < len(path_parts):
            # Get the next part after 'recipe/'
            recipe_slug = path_parts[i + 2] if i + 2 < len(path_parts) else path_parts[i + 1]
            # Remove ID numbers
            recipe_slug = "".join(c for c in recipe_slug if not c.isdigit())
            # Convert dashes/underscores to spaces and title case
            title = recipe_slug.replace("-", " ").replace("_", " ").strip()
            return title.title()
    return "Unknown Recipe"


def scrape_recipe(url):
    if "allrecipes.com" in url:
        i, d = scrape_allrecipes(url)
    elif "seriouseats.com" in url:
        i, d = scrape_seriouseats(url)
    return i, d


def scrape_allrecipes(url):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    # Ingredients
    ingredients = []
    for item in soup.select(".mm-recipes-structured-ingredients__list li"):
        ingredient = Ingredient(
            name=item.select_one("span[data-ingredient-name]").get_text(strip=True),
            quantity=item.select_one("span[data-ingredient-quantity]").get_text(strip=True),
            unit=res.get_text(strip=True)
            if (res := item.select_one("span[data-ingredient-unit]")) is not None
            else None,
            preparation=res.get_text(strip=True)
            if (res := item.select_one("span[data-ingredient-preparation]")) is not None
            else None,
        )

        # Catch any remaining text or spans as "misc"
        misc_parts = [
            t.strip()
            for t in item.stripped_strings
            if t.strip() not in {ingredient.quantity, ingredient.unit, ingredient.name, ingredient.preparation}
        ]
        if misc_parts:
            ingredient.misc = "".join(misc_parts)
        ingredients.append(ingredient)

    # Directions
    directions = []
    steps_section = soup.select_one("div#mm-recipes-steps_1-0")
    if steps_section:
        step_groups = steps_section.select(".comp.mntl-sc-block.mntl-sc-block-startgroup.mntl-sc-block-group--LI")
        for group in step_groups:
            html_blocks = group.select(".comp.mntl-sc-block.mntl-sc-block-html")
            for block in html_blocks:
                text = block.get_text(" ", strip=True)
                if text:
                    directions.append(text)

    return ingredients, directions


def scrape_seriouseats(url):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    # Ingredients
    ingredients = []
    for item in soup.select(".structured-ingredients__list-item"):
        i = Ingredient()
        for span in item.select(
            "span[data-ingredient-quantity], span[data-ingredient-unit], span[data-ingredient-name], span[data-ingredient-preparation]"  # noqa: E501
        ):
            if span.has_attr("data-ingredient-quantity") and i.quantity is None:
                i.quantity = span.get_text(strip=True)
            elif span.has_attr("data-ingredient-unit") and i.unit is None:
                i.unit = span.get_text(strip=True)
            elif span.has_attr("data-ingredient-name") and i.name is None:
                i.name = span.get_text(strip=True)
            elif span.has_attr("data-ingredient-preparation") and i.preparation is None:
                i.preparation = span.get_text(strip=True)

        # Catch any remaining text or spans as "misc"
        misc_parts = [
            t.strip() for t in item.stripped_strings if t.strip() not in {i.quantity, i.unit, i.name, i.preparation}
        ]
        if misc_parts:
            i.misc = " ".join(misc_parts)

        ingredients.append(i)

    # Directions
    directions = []
    steps_section = soup.select_one("div#structured-project__steps_1-0")

    if steps_section:
        directions = [
            d.get_text(" ", strip=True)
            for d in steps_section.select(".comp.mntl-sc-block.mntl-sc-block-html")
            if d.get_text(strip=True)
        ]

    return ingredients, directions
