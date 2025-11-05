import requests
from bs4 import BeautifulSoup
import re

# clean ingredients list a little bit
def fix_spacing(text):
    return re.sub(r'(?<=[\d¼½¾⅓⅔⅛⅜⅝⅞])(?=[A-Za-z])', ' ', text)

def scrape_recipe(url):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    # Ingredients
    ingredients = [
        fix_spacing(i.get_text(strip=True))
        for i in soup.select(".mm-recipes-structured-ingredients__list li")
    ]

    # Directions
    directions = []
    steps_section = soup.select_one("div#mm-recipes-steps_1-0")
    if steps_section:
        step_groups = steps_section.select(
            ".comp.mntl-sc-block.mntl-sc-block-startgroup.mntl-sc-block-group--LI"
        )
        for group in step_groups:
            html_blocks = group.select(".comp.mntl-sc-block.mntl-sc-block-html")
            for block in html_blocks:
                text = block.get_text(" ", strip=True)
                if text:
                    directions.append(text)

    return ingredients, directions
