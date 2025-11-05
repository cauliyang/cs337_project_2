import requests
from bs4 import BeautifulSoup
import re

# clean ingredients list a little bit
def fix_spacing(text):
    return re.sub(r'(?<=[\d¼½¾⅓⅔⅛⅜⅝⅞])(?=[A-Za-z])', ' ', text)

# URL to scrape
url = "https://www.allrecipes.com/recipe/220128/chef-johns-buttermilk-fried-chicken/"  # Replace with target URL

# get html
response = requests.get(url)
response.raise_for_status()
soup = BeautifulSoup(response.text, "html.parser")

# get ingredients and clean
ingredients = [
    fix_spacing(i.get_text(strip=True))
    for i in soup.select(".mm-recipes-structured-ingredients__list li")
]


# Directions: only HTML text blocks inside each LI group
steps_section = soup.select_one("div#mm-recipes-steps_1-0")
directions = []

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


print("Ingredients:")
for item in ingredients:
    print("-", item)

print("\nDirections:")
for i, step in enumerate(directions):
    print(f"Step {i+1}: {step}\n")
