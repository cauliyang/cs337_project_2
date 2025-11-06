import requests
from bs4 import BeautifulSoup
import re


class Ingredient:
    def __init__(self, quantity=None, unit=None, name=None, preparation=None, misc=None):
        self.quantity = quantity
        self.unit = unit
        self.name = name
        self.preparation = preparation
        self.misc = misc

    def __repr__(self):
        parts = []
        if self.quantity:
            parts.append(str(self.quantity))
        if self.unit:
            parts.append(self.unit)
        if self.name:
            parts.append(self.name)
        #if self.preparation:
            #parts.append(f"({self.preparation})")
        #if self.misc:
            #parts.append(f"{self.misc}")
        return " ".join(parts)


def scrape_recipe(url):
    if "allrecipes.com" in url:
        i, d = scrape_allrecipes(url)
    elif "seriouseats.com" in url:
        i, d = scrape_seriouseats(url)

    return i, d



########################## INDIVIDUAL WEBSITE SCRAPERS #################################

def scrape_allrecipes(url):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    # Ingredients
    ingredients = []
    for item in soup.select(".mm-recipes-structured-ingredients__list li"):
        i = Ingredient()
        for span in item.select("span[data-ingredient-quantity], span[data-ingredient-unit], span[data-ingredient-name], span[data-ingredient-preparation]"):
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
            t.strip()
            for t in item.stripped_strings
            if t.strip() not in {i.quantity, i.unit, i.name, i.preparation}
        ]
        if misc_parts:
            i.misc = "".join(misc_parts)

        ingredients.append(i)
        


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



def scrape_seriouseats(url):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    # Ingredients
    ingredients = []
    for item in soup.select(".structured-ingredients__list-item"):
        i = Ingredient()
        for span in item.select("span[data-ingredient-quantity], span[data-ingredient-unit], span[data-ingredient-name], span[data-ingredient-preparation]"):
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
            t.strip()
            for t in item.stripped_strings
            if t.strip() not in {i.quantity, i.unit, i.name, i.preparation}
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

